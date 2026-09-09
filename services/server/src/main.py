import os
import sys

import logger
import server

SERVER_HOST = os.environ["SERVER_HOST"]
SERVER_PORT = int(os.environ["SERVER_PORT"])
STORAGE_DIR = os.environ.get("STORAGE_DIR", "/tmp/bets.csv")
AGENCY_QUORUM_MIN = int(os.environ.get("AGENCY_QUORUM_MIN", 2))


def main():
    logger.init()
    s = server.Server(SERVER_HOST, SERVER_PORT, STORAGE_DIR, AGENCY_QUORUM_MIN)
    try:
        s.run()
    except Exception as e:
        logger.error("server-run", logger.LogResult.fail, "err", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
