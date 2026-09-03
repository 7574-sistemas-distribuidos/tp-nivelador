package domain

type Message struct {
	Header  MessageHeader
	Payload []byte
}
type MessageType uint8

const (
	MessageTypeRegisterAgency MessageType = iota + 1
	MessageTypeAck
	MessageTypeBet
	MessageTypeAwaitingWinners
)

func RegisterAgencyMessage(agency string) Message {
	return Message{
		Header: MessageHeader{
			Type:       MessageTypeRegisterAgency,
			PayloadLen: uint32(len(agency)),
		},
		Payload: []byte(agency),
	}
}

func AckMessage() Message {
	return Message{
		Header: MessageHeader{
			Type:       MessageTypeAck,
			PayloadLen: 0,
		},
		Payload: nil,
	}
}

func BetMessage(bet Bet) Message {
	payload := bet.Serialize()
	return Message{
		Header: MessageHeader{
			Type:       MessageTypeBet,
			PayloadLen: uint32(len(payload)),
		},
		Payload: payload,
	}
}

func AwaitingWinnersMessage() Message {
	return Message{
		Header: MessageHeader{
			Type:       MessageTypeAwaitingWinners,
			PayloadLen: 0,
		},
		Payload: nil,
	}
}
