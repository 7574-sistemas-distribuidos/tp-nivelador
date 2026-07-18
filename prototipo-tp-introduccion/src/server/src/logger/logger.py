import logging
from enum import StrEnum

class LogResult(StrEnum):
    in_progress = "in-progress"
    fail = "fail"
    success = "success"

def init():
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s %(levelname)s %(message)s",
		datefmt="%Y/%m/%d %H:%M:%S",
	)

def _parse_args(args) -> str:
	parsed_args = []
	for pair in zip(args[::2], args[1::2]):
		parsed_args.append(f"{pair[0]}={pair[1]}")
	return " ".join(parsed_args)

def info(action: str, result: LogResult, *args):
	logging.info(f"action={action} result={result} {_parse_args(args)}")

def error(action: str, result: LogResult, *args):
	logging.error(f"action={action} result={result} {_parse_args(args)}")
