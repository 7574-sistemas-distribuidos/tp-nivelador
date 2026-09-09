package protocol

import ( 
	"net" 
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket" 
)

const (
	REQUEST PacketType = iota 
	RESPONSE  
	EOF  
	INIT
	ACK
)

func SendInit(conn net.Conn, seqNum int, payload []byte) error {
	packet := NewPacket(INIT, seqNum, payload)
	packetBytes := packet.ToBytes()
	return safe_socket.SendAll(conn, packetBytes)
}

func SendRequest(conn net.Conn, seqNum int, payload []byte) error {
	packet := NewPacket(REQUEST, seqNum, payload)
	packetBytes := packet.ToBytes()
	return safe_socket.SendAll(conn, packetBytes)
}


func SendResponse(conn net.Conn, seqNum int, payload []byte) error {
	packet := NewPacket(RESPONSE, seqNum, payload)
	packetBytes := packet.ToBytes()
	return safe_socket.SendAll(conn, packetBytes)
}

func SendEOF(conn net.Conn, seqNum int) error {
	packet := NewPacket(EOF, seqNum, []byte{})
	packetBytes := packet.ToBytes()
	return safe_socket.SendAll(conn, packetBytes)
}

func SendACK(conn net.Conn, seqNum int, payload []byte) error {
	packet := NewPacket(ACK, seqNum, payload)
	packetBytes := packet.ToBytes()
	return safe_socket.SendAll(conn, packetBytes)
}

func ReceiveFrom(conn net.Conn) (*Packet, error) {
	header, err := safe_socket.RecvAll(conn, HEADER_SIZE)
	if err != nil {
		return nil, err
	}

	pktType := PacketType(header[:1][0])
	seqNumber := decode(header[1:5])
	payloadSize := decode(header[5:])

	
	payload, err := safe_socket.RecvAll(conn, payloadSize)
	if err != nil {
		return nil, err
	}

	return &Packet{
		packetType: pktType,
		sequenceNumber: seqNumber,
		payload: payload,
	}, nil
}
