import os
import sys
import signal

import logger
import server

SERVER_HOST = os.environ["SERVER_HOST"]
SERVER_PORT = int(os.environ["SERVER_PORT"])


def main():
    logger.init()
    s = server.Server(SERVER_HOST, SERVER_PORT)

    def handle_sigterm(signum, frame):
        logger.info("sigterm-received", logger.LogResult.in_progress, "signum", signum)
        s.shutdown()

    signal.signal(signal.SIGTERM, handle_sigterm)

    try:
        s.run()
    except Exception as e:
        logger.error("server-run", logger.LogResult.fail, "err", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())