package protocol

type MessageType uint8

const (
	BetMessage MessageType = iota
	AckBetMessage
	AllBetsSentMessage
	WinnersMessage
)
