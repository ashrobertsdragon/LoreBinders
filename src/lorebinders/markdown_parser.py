def markdown_to_dict(markdown_str: str) -> dict:
    result_dict: dict = {}
    stack: list[dict] = [result_dict]
    current_key: str | None = None
    current_list: list | None = None

    for line in markdown_str.splitlines():
        stripped_line = line.strip()

        if stripped_line.startswith("#"):
            level = stripped_line.count("#")
            key = stripped_line[level:].strip()

            while len(stack) > level:
                stack.pop()

            new_dict: dict = {}
            if len(stack) == level:
                if current_key:
                    stack[-1][current_key] = new_dict
                else:
                    stack[-1][key] = new_dict
                current_key = key
                current_list = None
            stack.append(new_dict)
        elif stripped_line.startswith("- "):
            if current_key and isinstance(stack[-1], dict):
                if current_list is None:
                    current_list = []
                    stack[-1][current_key] = current_list
                value = stripped_line[2:].strip()
                current_list.append(value)

    return result_dict
