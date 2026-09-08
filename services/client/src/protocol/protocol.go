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
)

func SendInit(conn net.Conn, payload []byte) error {
	packet := NewPacket(INIT, payload)
	packetBytes := packet.ToBytes()
	return safe_socket.SendAll(conn, packetBytes)
}

func SendRequest(conn net.Conn, payload []byte) error {
	packet := NewPacket(REQUEST, payload)
	packetBytes := packet.ToBytes()
	return safe_socket.SendAll(conn, packetBytes)
}


func SendResponse(conn net.Conn, payload []byte) error {
	packet := NewPacket(RESPONSE, payload)
	packetBytes := packet.ToBytes()
	return safe_socket.SendAll(conn, packetBytes)
}

func SendEOF(conn net.Conn) error {
	packet := NewPacket(EOF, []byte{})
	packetBytes := packet.ToBytes()
	return safe_socket.SendAll(conn, packetBytes)
}

func ReceiveFrom(conn net.Conn) (*Packet, error) {
	header, err := safe_socket.RecvAll(conn, HEADER_SIZE)
	if err != nil {
		return nil, err
	}

	pktType := PacketType(header[:1][0])
	payloadSize := decode(header[1:])
	
	payload, err := safe_socket.RecvAll(conn, payloadSize)
	if err != nil {
		return nil, err
	}

	return &Packet{
		packetType:    pktType,
		payload: payload,
	}, nil
}
