class Packet:
    LENGTH_MESSAGE_SIZE = 4
    HEADER_SIZE = 1 + LENGTH_MESSAGE_SIZE 

    def __init__(self, packet_type, payload):
        self._packet_type = packet_type
        self._payload = payload

    def type(self):
        return self._packet_type

    def payload(self):
        return self._payload

    def payload_size(self):
        return len(self._payload)

    def payload_to_string(self):
        return self._payload.decode('utf-8')
    
    def to_bytes(self):
        packet_type_bytes = self._packet_type.to_bytes(1, byteorder='big')
        payload_size_bytes = self.payload_size().to_bytes(4, byteorder='big')
        return packet_type_bytes + payload_size_bytes + self._payload

