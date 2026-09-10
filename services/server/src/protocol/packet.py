class Packet:
    SEQUENCE_NUMBER_BYTES = 4
    LENGTH_MESSAGE_SIZE = 4
    HEADER_SIZE = 1 + SEQUENCE_NUMBER_BYTES + LENGTH_MESSAGE_SIZE 

    def __init__(self, packet_type, sequence_number, payload):
        self._packet_type = packet_type
        self._sequence_number = sequence_number
        self._payload = payload

    def type(self):
        return self._packet_type

    def sequence_number(self):
        return self._sequence_number

    def payload_size(self):
        return len(self._payload)

    def payload(self):
        return self._payload

    def payload_to_string(self):
        return self._payload.decode('utf-8')
    
    def to_bytes(self):
        packet_type_bytes = self._packet_type.to_bytes(1, byteorder='big')
        sequence_number_bytes = self._sequence_number.to_bytes(4, byteorder='big')
        payload_size_bytes = self.payload_size().to_bytes(4, byteorder='big')
        return packet_type_bytes + sequence_number_bytes + payload_size_bytes + self._payload

