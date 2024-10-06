"""
Supabase model handler for AI models.

Usage:
    from lorebinders.ai.ai_models import SupaSaaSAIProviderHandler, init_db

    handler = SupaSaaSAIProviderHandler(init_db())

    # Access the AIModelRegistry
    registry = handler.registry
"""

from collections.abc import Callable

from supasaas import SupabaseClient, SupabaseDB, SupabaseLogin

from lorebinders.ai.ai_models._model_schema import AIModelRegistry
from lorebinders.ai.ai_models.sql_provider_handler import SQLProviderHandler


def init_db() -> SupabaseDB:
    """
    Initialize a Supabase database client from environment variables.

    Returns:
        SupabaseDB: An instance of the SupabaseDB class.
    """
    login = SupabaseLogin.from_config()
    client = SupabaseClient(login)
    return SupabaseDB(client)


class SupaSaaSAIProviderHandler(SQLProviderHandler):
    """SQL database handler for AI model data using Supabase."""

    query_templates: dict[str, dict] = {
        "insert": {
            "providers": ["api"],
            "ai_families": ["family", "tokenizer", "provider_api"],
            "models": [
                "id",
                "name",
                "api_model",
                "context_window",
                "rate_limit",
                "family",
            ],
        },
        "update": {
            "models": ["name", "api_model", "context_window", "rate_limit"]
        },
        "delete": {
            "providers": ["api"],
            "ai_families": ["provider_api"],
            "models": ["id", "family"],
        },
        "select": {
            "providers": "api",
            "ai_families": "provider_api",
            "models": "family",
        },
    }

    def __init__(self, db: SupabaseDB):
        self.db = db
        self._registry: AIModelRegistry | None = None

    def _fetch_rows(self, table_name: str, match_column: str) -> list[dict]:
        """
        Fetches all rows from the given table that have a non-null value in the
        given column.

        Args:
            table_name (str): The name of the table to query.
            match_column (str): The column to match. Rows with a null value in
                this column will be excluded from the results.

        Returns:
            list[dict]: A list of dictionaries, where each dictionary is a
                row in the table. Each dictionary key is a column name, and
                each dictionary value is the value of that column in the row.
        """
        return self.db.select_row(
            table_name=table_name,
            match={match_column: "IS NOT NULL"},
            match_type=str,
            use_service_role=True,
        )

    def _registry_query(self) -> list[dict]:
        """
        Queries the database for all the data needed to construct the
        AIModelRegistry.

        Returns:
            list[dict]: A list of dictionaries, where each dictionary is a row
                in one of the three tables. Each dictionary key is a column
                name, and each dictionary value is the value of that column in
                the row.
        """
        registry_data = self._fetch_rows("providers", "api")
        registry_data.extend(self._fetch_rows("ai_families", "provider_api"))
        registry_data.extend(self._fetch_rows("models", "name"))
        return registry_data

    def _load_registry(self) -> AIModelRegistry:
        """
        Loads the AIModelRegistry from the database.

        Returns:
            AIModelRegistry: The AIModelRegistry constructed from the database.
        """

        db_response = self._registry_query()
        registry_data = self._process_db_response(db_response)
        return AIModelRegistry.model_validate(registry_data)

    def _get_match_params(self, action: str, table: str) -> list[str]:
        """
        Returns the list of column names to match for the given action and
        table.

        Args:
            action (str): The name of the action to perform.
            table (str): The name of the table to perform the action on.

        Returns:
            list[str]: The list of column names to match.
        """
        return self.query_templates[action][table]

    def _prepare_insert(
        self, params: tuple, match_params: list[str]
    ) -> tuple[dict, dict]:
        """
        Prepares the data for insertion into the database.

        Args:
            params (tuple): The data to insert.
            match_params (list[str]): The column names to match.

        Returns:
            tuple[dict, dict]: A tuple containing the data to insert as a
                dictionary and an empty dictionary as the match parameters.
        """
        return dict(zip(match_params, params, strict=False)), {}

    def _prepare_update(
        self, params: tuple, match_params: list[str]
    ) -> tuple[dict, dict]:
        """
        Prepares the data for updating in the database.

        Args:
            params (tuple): The data to update.
            match_params (list[str]): The column names to match.

        Returns:
            tuple[dict, dict]: A tuple containing the data to update as a
                dictionary, and the match parameters as a dictionary. The
                key in the data dictionary is the first element of
                match_params, and the values are the remaining elements of
                params. The key in the match dictionary is the first element
                of match_params, and the value is the first element of
                params.
        """

        return {match_params[0]: params[0]}, dict(
            zip(match_params[1:], params[1:], strict=False)
        )

    def _prepare_delete(
        self, params: tuple, match_params: list[str]
    ) -> tuple[dict, dict]:
        """
        Prepares the data for deletion from the database.

        Args:
            params (tuple): The data to delete.
            match_params (list[str]): The column names to match.

        Returns:
            tuple[dict, dict]: A tuple containing the match parameters as a
                dictionary and the data to delete as a dictionary. The key in
                the data dictionary is the first element of match_params, and
                the value is the first element of params.
        """
        return {match_params[0]: params[0]}, {}

    def _prepare_data(
        self, action: str, table: str, params: tuple
    ) -> tuple[dict, dict]:
        """
        Prepares the data for an operation in the database.

        Args:
            action (str): The operation to perform on the database.
            table (str): The table to operate on.
            params (tuple): The data to operate on.

        Returns:
            tuple[dict, dict]: A tuple containing the data to operate on as a
                dictionary, and the match parameters as a dictionary. The
                key in the data dictionary is the first element of
                match_params, and the values are the remaining elements of
                params. The key in the match dictionary is the first element
                of match_params, and the value is the first element of
                params.
        """
        match_params = self._get_match_params(action, table)
        prepare_strategies: dict[
            str, Callable[[tuple, list[str]], tuple[dict, dict]]
        ] = {
            "insert": self._prepare_insert,
            "update": self._prepare_update,
            "delete": self._prepare_delete,
        }

        return prepare_strategies[action](params, match_params)

    def _execute_insert(
        self, table: str, data: dict, match: dict, use_service_role: bool
    ) -> bool:
        """
        Executes an insert operation on the database.

        Args:
            table (str): The name of the table to insert into.
            data (dict): The data to insert into the table.
            match (dict): Unused.
            use_service_role (bool): Whether to use the service role.

        Returns:
            bool: True if the insert was successful, False otherwise.
        """
        return self.db.insert_row(
            table_name=table, data=data, use_service_role=use_service_role
        )

    def _execute_update(
        self,
        table: str,
        data: dict,
        match: dict,
        match_type: type,
        use_service_role: bool,
    ) -> bool:
        """
        Executes an update operation on the database.

        Args:
            table (str): The name of the table to update.
            data (dict): The data to update in the table.
            match (dict): The match parameters for the update.
            match_type (type): The type of the match parameters.
            use_service_role (bool): Whether to use the service role.

        Returns:
            bool: True if the update was successful, False otherwise.
        """

        return self.db.update_row(
            table_name=table,
            info=data,
            match=match,
            match_type=match_type,
            use_service_role=use_service_role,
        )

    def _execute_delete(
        self, table: str, match: dict, match_type: type, use_service_role: bool
    ) -> bool:
        """
        Executes a delete operation on the database.

        Args:
            table (str): The name of the table to delete from.
            match (dict): The match parameters for the delete.
            match_type (type): The type of the match parameters.
            use_service_role (bool): Whether to use the service role.

        Returns:
            bool: True if the delete was successful, False otherwise.
        """

        return self.db.delete_row(
            table_name=table,
            match=match,
            match_type=match_type,
            use_service_role=use_service_role,
        )

    def _execute_query(
        self, action: str, table: str, data: dict, match: dict
    ) -> bool:
        """
        Executes a query on the database.

        Args:
            action (str): The query type to execute (insert, update, delete).
            table (str): The name of the table to query.
            data (dict): The data to insert or update.
            match (dict): The match parameters for the query.

        Returns:
            bool: True if the query was successful, False otherwise.
        """
        use_service_role = True
        match_type = type(next(iter(match.values()), None))

        execute_strategies: dict[str, Callable] = {
            "insert": self._execute_insert,
            "update": self._execute_update,
            "delete": self._execute_delete,
        }

        return execute_strategies[action](
            table, data, match, match_type, use_service_role
        )

    def _query_db(self, action: str, table: str, params: tuple) -> list:
        """
        Queries the database based on the given action and table.

        Args:
            action (str): The query type to execute (insert, update, delete).
            table (str): The name of the table to query.
            params (tuple): The parameters for the query.

        Returns:
            list: A list containing a single string. If query is successful,
                the string is "success". Otherwise, the string is "failure".
                This is to maintain compatibility with the other handlers that
                return a list while SupaSaaS abstracts it away.

        """
        data, match = self._prepare_data(action, table, params)
        if self._execute_query(action, table, data, match):
            return ["success"]
        return ["failure"]
