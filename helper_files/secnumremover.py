import re


def replace_match_with(text: str, pattern: str, replace_with: str) -> str:
    """pattern is a regex. replace all matches of pattern
    in text with replace_with."""
    return re.sub(pattern, replace_with, text)
