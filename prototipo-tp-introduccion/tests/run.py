import sys
import logging

from tests import OutputFiles, SigtermHandling, Concurrency, Json, TestCase

DOCKER_COMPOSE_PATH = "./docker-compose.yaml"
TEST_CASES: list[TestCase] = [OutputFiles(), SigtermHandling(), Concurrency(), Json()]


def main():
    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y/%m/%d %H:%M:%S",
        format=f"%(asctime)s %(levelname)s %(message)s",
    )
    exit_code = 0
    for test_case in TEST_CASES:
        logging.info(f"test={test_case.name} result=in-progress")
        try:
            test_case.test(
                lambda msg: logging.info(
                    f"test={test_case.name} result=in-progress msg={msg}"
                ),
                DOCKER_COMPOSE_PATH,
            )
            logging.info(f"test={test_case.name} result=success")
        except Exception as e:
            logging.error(f"test={test_case.name} result=fail err={e}")
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
