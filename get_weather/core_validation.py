import re


def is_invalid_city_name(value: str) -> bool:
    if not value or value.isspace():
        return True
    if any(char.isdigit() for char in value):
        return True
    return re.search(r"[a-zA-Z]+$", value) is not None
