from typing import Any


def dict_safe_equals(source: dict, key: str, expectation: Any):
    """
    Checks if the dictionary has a key AND the value matches the expectation.
    This will FAIL if the dictionary does not have the key to begin with
    (i.e., you cannot force-match with default value.)

    :param source: source dictionary
    :param key: key to look in source
    :param expectation: expected value
    """
    return key in source and source[key] == expectation
