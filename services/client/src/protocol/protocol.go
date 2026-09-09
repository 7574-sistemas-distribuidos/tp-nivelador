package protocol

import ( 
	"net" 
	"fmt"
	"strings"
	"strconv"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket" 
)

const (
	REQUEST PacketType = iota 
	RESPONSE  
	EOF  
	INIT
	ACK
)

const BET_FIELDS = 5

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

func ParseBetFromCSVLine(line string, agencyId string) (*Bet, error) {
    line = strings.TrimSpace(line)
    if line == "" {
        return nil, fmt.Errorf("Parsing Error: empty line")
    }
 
    fields := strings.Split(line, ",")
    if len(fields) != BET_FIELDS {
        return nil, fmt.Errorf("Parsing Error: se esperaban 5 campos, se obtuvieron %d", len(fields))
    }
  
    firstName := fields[0]
    lastName := fields[1]

    document, err := strconv.Atoi(fields[2])
    if err != nil {
        return nil, fmt.Errorf("Parsing Error: invalid 'Documento' number: %v", err)
    }

    birthdate := fields[3]

    number, err := strconv.Atoi(fields[4])
    if err != nil {
        return nil, fmt.Errorf("Parsing Error: invalid 'Number': %v", err)
    }
 
    return NewBet(agencyId, firstName, lastName, document, birthdate, number), nil
}

func ParseCSVLineFromBet(bet Bet) (string, error) {
    return fmt.Sprintf("%s,%s,%d,%s,%d", bet.firstName, bet.lastName, bet.document, bet.birthdate, bet.number), nil
}
