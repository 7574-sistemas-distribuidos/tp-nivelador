import sys
from tests import (
    OutputFiles,
    SigtermHandling,
    Concurrency,
    Json,
    ForcedExit,
    Batching,
    MemoryProfile,
    ServerShortReadWrite,
    ClientShortReadWrite,
)

TEST_CASES = [
    Batching,
    ClientShortReadWrite,
    Concurrency,
    ForcedExit,
    Json,
    MemoryProfile,
    OutputFiles,
    ServerShortReadWrite,
    SigtermHandling,
]
MESSAGE_PADDING = 32


def main():
    for test_case in TEST_CASES:
        print(f"Testing {test_case.title.ljust(MESSAGE_PADDING, ".")}", end="")
        try:
            test_case.test()
            print("OK")
        except Exception as e:
            print("ERROR")
            print(f"{e}", file=sys.stderr, end="\n\n")
            print(f"HINT: {test_case.error_hint}", file=sys.stderr, end="\n\n")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
