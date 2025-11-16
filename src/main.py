"""Main module for the template project."""


def main() -> None:
    """Print hello."""
    a = 5
    b = 10  # expected: Local variable `b` is assigned to but never used # noqa: F841
    print(a)  # expected: 'print' found # noqa: T201


if __name__ == "__main__":
    main()
