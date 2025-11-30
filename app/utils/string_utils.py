from typing import List


def str_in_list_ignore_case(s: str, l: List[str]):
    return s.lower() in [l.lower() for l in l]
