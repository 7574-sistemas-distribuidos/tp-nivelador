import sys
from tests import OutputFiles, SigtermHandling, Concurrency, Json, ForcedExit, Batching

TEST_CASES = [Json, ForcedExit, OutputFiles, Batching, Concurrency, SigtermHandling]
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
            print(f"{e}", file=sys.stderr, end="\n\n")
            print(f"HINT: {test_case.error_hint}", file=sys.stderr, end="\n\n")
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
