import os
import sys
import logging

from src.server import Server

SERVER_HOST = os.environ["SERVER_HOST"]
SERVER_PORT = int(os.environ["SERVER_PORT"])


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )
    server = Server(SERVER_HOST, SERVER_PORT)
    try:
        server.run()
    except Exception as e:
        logging.error(e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
