package protocol

import "fmt"

const INT32_BYTES = 4 
const STRING_LEN_PREFIX_SIZE = 2 

// Bet representa una apuesta con sus datos
type Bet struct {
	agencyId string
    firstName string
    lastName string
    document int
    birthdate string
    number int
}	

// New crea una nueva apuesta
func NewBet(agencyId string, firstName string, lastName string, document int, birthdate string, number int) *Bet {
		return &Bet{
			agencyId:  agencyId,
			firstName: firstName,
			lastName:  lastName,
			document:  document,
			birthdate: birthdate,
			number:    number,
		}
	}

// ToBytes convierte la apuesta a []byte. 
func (b *Bet) ToBytes() []byte {
	totalSize := INT32_BYTES * 2 + 	//  document, number
		STRING_LEN_PREFIX_SIZE + len(b.agencyId) +
		STRING_LEN_PREFIX_SIZE + len(b.firstName) +
		STRING_LEN_PREFIX_SIZE + len(b.lastName) +
		STRING_LEN_PREFIX_SIZE + len(b.birthdate) 

	bytes := make([]byte, 0, totalSize)

	bytes = append(bytes, stringToBytes(b.agencyId)...)
	bytes = append(bytes, stringToBytes(b.firstName)...)
	bytes = append(bytes, stringToBytes(b.lastName)...)
	bytes = append(bytes, intToBytes(b.document, INT32_BYTES)...)
	bytes = append(bytes, stringToBytes(b.birthdate)...)
	bytes = append(bytes, intToBytes(b.number, INT32_BYTES)...)

	return bytes
}

// FromBytes crea una apuesta (Bet) desde un slice de bytes.
func (b *Bet) FromBytes(data []byte) error {
	minSize := INT32_BYTES*2 + STRING_LEN_PREFIX_SIZE*4
	if len(data) < minSize {
		return fmt.Errorf("Parsing Bet Error: bytes length too short: %v", len(data))
	}

	idx := 0
	var prefix int
	var err error
	b.agencyId, prefix, err = bytesToString(data[idx:], STRING_LEN_PREFIX_SIZE)
	if err != nil { return err }
	idx += prefix
	b.firstName, prefix, err = bytesToString(data[idx:], STRING_LEN_PREFIX_SIZE)
	if err != nil { return err }
	idx += prefix
	b.lastName, prefix, err = bytesToString(data[idx:], STRING_LEN_PREFIX_SIZE)
	if err != nil { return err }
	idx += prefix
	b.document = bytesToInt(data[idx:idx+INT32_BYTES], INT32_BYTES)
	idx += INT32_BYTES
	b.birthdate, prefix, err = bytesToString(data[idx:], STRING_LEN_PREFIX_SIZE)
	if err != nil { return err }
	idx += prefix
	b.number = bytesToInt(data[idx:idx+INT32_BYTES], INT32_BYTES)
	return nil
}

// intToByte construye un slice de bytes a partir de un entero en Big Endian, usando exactamente cantBytes bytes
func intToBytes(num int, cantBytes int) []byte {
	b := make([]byte, cantBytes)
	for i := 0; i < cantBytes; i++ {
		shift := 8*(cantBytes-1-i)
		b[i] = byte(num >> shift)
	}
	return b
}

// stringToBytes serializa un string con prefijo de longitud (2 bytes en Big Endian).
func stringToBytes(str string) []byte {
	b := make([]byte, 0, STRING_LEN_PREFIX_SIZE+len(str))
	b = append(b, intToBytes(len(str), STRING_LEN_PREFIX_SIZE)...)
	b = append(b, str...)
	return b
}

// bytesToUint reconstruye un entero a partir de un slice de bytes en Big Endian.
func bytesToInt(data []byte, cantBytes int) int {
	num := 0 
	for i := 0; i < cantBytes; i++ {
		shift := 8*(cantBytes-1-i)
		num |= int(data[i]) << shift
	}
	return num
}

func bytesToString(data []byte, idx int) (string, int, error) {
    if len(data) < idx {
        return "", 0, fmt.Errorf("prefijo de longitud incompleto")
    }
	length := bytesToInt(data[:idx], idx)
    if len(data) < idx+length {
        return "", 0, fmt.Errorf("string incompleto: esperado %d bytes, disponibles %d", length, len(data)-idx)
    }
	str := string(data[idx: idx+length])
	return str, idx+len(str), nil
}
