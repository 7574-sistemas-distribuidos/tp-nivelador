import sys
import logging

from tests import OutputFiles, SigtermHandling, TestCase

DOCKER_COMPOSE_PATH = "./docker-compose.yaml"
TEST_CASES: list[TestCase] = [OutputFiles(), SigtermHandling()]


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
        except Exception as e:
            logging.error(f"test={test_case.name} result=success err={e}")
            exit_code = 1
        logging.info(f"test={test_case.name} result=success")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
