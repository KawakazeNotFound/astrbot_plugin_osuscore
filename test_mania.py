"""/mania 参数解析测试。"""

from utils import parse_mania_command_args


def run_tests() -> None:
    cases = [
        (
            "",
            {
                "username": None,
                "scope": "recent",
                "limit": 1,
                "variant": None,
                "mods": [],
            },
        ),
        (
            "peppy",
            {
                "username": "peppy",
                "scope": "recent",
                "limit": 1,
                "variant": None,
                "mods": [],
            },
        ),
        (
            "36148327",
            {
                "username": "36148327",
                "scope": "recent",
                "limit": 1,
                "variant": None,
                "mods": [],
            },
        ),
        (
            "peppy best 5",
            {
                "username": "peppy",
                "scope": "best",
                "limit": 5,
                "variant": None,
                "mods": [],
            },
        ),
        (
            "36148327 best 2",
            {
                "username": "36148327",
                "scope": "best",
                "limit": 2,
                "variant": None,
                "mods": [],
            },
        ),
        (
            "best 3 4k +HDDT",
            {
                "username": None,
                "scope": "best",
                "limit": 3,
                "variant": "4k",
                "mods": ["HD", "DT"],
            },
        ),
        (
            "l i l a c recent 2 7k +hd",
            {
                "username": "l i l a c",
                "scope": "recent",
                "limit": 2,
                "variant": "7k",
                "mods": ["HD"],
            },
        ),
    ]

    for i, (input_text, expected) in enumerate(cases, start=1):
        actual = parse_mania_command_args(input_text)
        assert actual == expected, f"Case {i} failed\ninput: {input_text}\nactual: {actual}\nexpected: {expected}"

    print("[OK] mania 参数解析测试全部通过")


if __name__ == "__main__":
    run_tests()
