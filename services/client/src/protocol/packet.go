package protocol

const SEQUENCE_NUMBER_BYTES = 4
const LENGTH_MESSAGE_SIZE = 4
const HEADER_SIZE = 1 + SEQUENCE_NUMBER_BYTES + LENGTH_MESSAGE_SIZE 

type PacketType byte

type Packet struct {
	packetType PacketType
	sequenceNumber int
	payload []byte
}	

func NewPacket(packetType PacketType, sequenceNumber int, payload []byte) *Packet {
	return &Packet{
		packetType: packetType,
		sequenceNumber: sequenceNumber,
		payload: payload,
	}
}

func (p *Packet) Type() PacketType {
	return p.packetType
}

func (p *Packet) SequenceNumber() int {
	return p.sequenceNumber
}

func (p *Packet) PayloadSize() int {
	return len(p.payload)
}

func (p *Packet) Payload() []byte {
	return p.payload
}

func (p *Packet) ToBytes() []byte {
	packet := make([]byte, 0, HEADER_SIZE+p.PayloadSize())
	packet = append(packet, byte(p.Type()))
	packet = append(packet, encode(p.SequenceNumber(), SEQUENCE_NUMBER_BYTES)...)
	packet = append(packet, encode(p.PayloadSize(), LENGTH_MESSAGE_SIZE)...)
	packet = append(packet, p.Payload()...)
	return packet
}

func encode(payloadSize int, cantBytes int) []byte {
	/* 	
		encode construye un slice de bytes
		a partir de un entero en Big Endian 
	*/

	length_msg := make([]byte, cantBytes)
	for i := 0; i < cantBytes; i++ {
		shift := 8*(cantBytes-1-i)
		length_msg[i] = byte(payloadSize >> shift)
	}
	return length_msg
}

func decode(length_msg []byte) int {
	/* 	
		decode reconstruye un entero 
		a partir de un slice de bytes 
		en Big Endian
	*/ 

	payloadSize := 0
	cantBytes := len(length_msg)
	for i := 0; i < cantBytes; i++ {
		shift := 8*(cantBytes-1-i)
		payloadSize |= int(length_msg[i]) << shift
	}
	return payloadSize
}