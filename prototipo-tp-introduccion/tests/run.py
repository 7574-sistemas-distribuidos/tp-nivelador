import sys
from tests import OutputFiles, SigtermHandling, Concurrency, Json, ForcedExit

TEST_CASES = [Json, ForcedExit, OutputFiles, SigtermHandling, Concurrency]
MESSAGE_PADDING = 32


def main():
    exit_code = 0
    for test_case in TEST_CASES:
        print(f"Testing {test_case.title.ljust(MESSAGE_PADDING, ".")}", end="")
        try:
            test_case.test()
            print("OK")
        except Exception as e:
            print("ERROR")
            print(f"ERROR: {e}", file=sys.stderr)
            print(f"\nHINT: {test_case.error_hint}\n", file=sys.stderr)
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
