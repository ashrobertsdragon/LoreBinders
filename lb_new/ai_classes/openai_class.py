import logging
import os
import time
from typing import Optional

from openai import OpenAI

from ai_interface import AIInterface
from exceptions import NoMessageError
from error_handler import ErrorHandler
from file_handling import FileHandler
from json_repair import JSONRepair

errors = ErrorHandler()
files = FileHandler()
repair = JSONRepair()

class OpenAIAPI(AIInterface):
    """
    Child class of AIInterface.
    """
    def __init__(self):
        super().__init__()
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            errors.kill_app("OPENAI_API_KEY environment variable not set")
        self.openai_client = OpenAI()

    def call_api(self, api_payload: dict, retry_count: Optional[int] = 0, assistant_message: Optional[str] = None, json_response: Optional[bool] = False) -> str:
        super().call_api()
        response_format = {"type": "json_object"} if json_response else {"type": "text"}

        try:
            response = self.make_api_call(api_payload, messages, response_format)
            content = self.process_response(response, json_response)
        except Exception as e:
            retry_count = self.error_handle(e, retry_count)
            content = self.call_api(api_payload, retry_count, assistant_message, json_response)

        answer = self.postprocess_response(content, assistant_message, api_payload, retry_count, json_response)
        return answer

    def make_api_call(self, api_payload, messages, response_format):
        response = self.openai_client.chat.completions.create(
            model=api_payload["model_name"],
            messages=messages,
            temperature=api_payload["temperature"],
            max_tokens=api_payload["max_tokens"],
            response_format=response_format
        )
        return response

    def process_response(self, response):
        if response.choices and response.choices[0].message.content:
            content = response.choices[0].message.content.strip()
            tokens = response.usage.total_tokens
            self.rate_limit_data["tokens_used"] += tokens
            self.files.write_json_file(self.rate_limit_data, "rate_limit_data.json")
        else:
            logging.error("No message content found")
            raise NoMessageError("No message content found")

        return content

    def postprocess_response(self, content, assistant_message, api_payload, retry_count, json_response):
        if assistant_message:
            if json_response:
                new_part = content[1:]
                combined = repair.merge(assistant_message, new_part)
                if combined:
                    answer = combined
                else:
                    answer = repair.repair(assistant_message + new_part)
            else:
                answer = assistant_message + content
        else:
            answer = content

        if response.choices[0].finish_reason == "length":
            length_warning = f"Max tokens exceeded.\nUsed {completion_tokens} of {max_tokens}"
            logging.warning(length_warning)
            if json_response:
                last_complete = answer.rfind("},")
                assistant_message = answer[:last_complete + 1] if last_complete > 0 else ""
            else:
                assistant_message = answer
            api_payload = self.modify_payload(api_payload, max_tokens=500)
            answer = self.call_api(api_payload, retry_count, assistant_message, json_response)

        return answer