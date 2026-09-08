package protocol

type Header struct {
	AgencyId    uint8
	MessageType MessageType
}

func NewHeader(agencyId uint8, messageType MessageType) Header {
	return Header{
		AgencyId:    agencyId,
		MessageType: messageType,
	}
}

func (h Header) Serialize() []byte {
	return []byte{byte(h.MessageType), h.AgencyId}
}

func (h Header) Size() int {
	return 2
}
