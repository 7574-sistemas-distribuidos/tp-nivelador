import os
import re
import sys

PACKET_LENGTH_MIN = 40
PACKET_LENGTH_REGEX = r"(?<=length )(\d)+"


def main():
    packet_count = 0
    packet_total_length = 0
    packet_length_pattern = re.compile(PACKET_LENGTH_REGEX)
    for line in sys.stdin:
        match = packet_length_pattern.search(line)
        if not match:
            continue
        packet_length = int(match.group(0))
        if packet_length < PACKET_LENGTH_MIN:
            continue
        packet_count += 1
        packet_total_length += packet_length
        print(packet_total_length / packet_count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
