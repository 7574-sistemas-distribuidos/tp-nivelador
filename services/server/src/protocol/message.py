class StartBetWinnersSendingMessage:
    def to_bytes(self):
        return self._type() + self._length() + self._payload()

    def _type(self):
        return b"\x04"

    def _length(self):
        return b"\x00\x00"

    def _payload(self):
        return b""
