package protocol

/* HEADER (3 bytes)
  tipo:          1 byte
  largo payload: 2 bytes

PAYLOAD BATCH (variable, tamaño = largo payload)
  agency:        1 byte
  bets:          repetido, cada uno:
    largo nombre:  1 byte
    nombre:        N bytes   (UTF-8, variable)
    largo apellido:1 byte
    apellido:      M bytes   (UTF-8, variable)
    documento:     4 bytes
    cumpleaños:    4 bytes  (AAAAMMDD como un solo entero)
    number:        4 bytes

header type:
1 = BET       (cliente → servidor, una apuesta)
4 = END       (cliente → servidor, servidor → cliente, "ya mande todo")
2 = WINNER   (servidor → cliente, un winner)
3 = ACK   (cliente → servidor, servidor → cliente, confirmación de exito, sin payload)
5 = BATCH ( client -> servidor)
*/

import (
	"encoding/binary"
	"fmt"
	"net"
	"strconv"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

const Winner = 2
const Ack = 3
const End = 4
const Batch = 5
const headerSize = 3
const MaxPayloadSize = 0xFFFF
const MaxFieldLength = 0xFF

type WinnerMessage struct {
	Name      string
	Lastname  string
	Document  uint32
	Birthdate string
	Number    uint32
}

func ReadMessage(sock net.Conn) (int, []byte, error) {
	header, err := safe_socket.RecvAll(sock, headerSize)

	if err != nil {
		return 0, nil, err
	}

	tipo := int(header[0])
	largo_payload := int(binary.BigEndian.Uint16(header[1:3]))
	payload, err := safe_socket.RecvAll(sock, largo_payload)

	if err != nil {
		return 0, nil, err
	}

	return tipo, payload, nil
}

func EncodeEnd() []byte {
	return newMessage(End, 0)
}

func EncodeAck() []byte {
	return newMessage(Ack, 0)
}

// codifica una apuesta y la agrega al final del buf
// se usa para acumular apuestas dentro de un batch
func AppendBet(buf []byte, name, lastname, birthdate []byte, document, number uint32) ([]byte, error) {
	buf, err := appendFixedField(buf, name)

	if err != nil {
		return nil, fmt.Errorf("name: %w", err)
	}

	buf, err = appendFixedField(buf, lastname)

	if err != nil {
		return nil, fmt.Errorf("lastname: %w", err)
	}

	birthdateValue, err := encodeBirthdate(birthdate)
	if err != nil {
		return nil, fmt.Errorf("birthdate: %w", err)
	}

	buf = binary.BigEndian.AppendUint32(buf, document)
	buf = binary.BigEndian.AppendUint32(buf, birthdateValue)
	buf = binary.BigEndian.AppendUint32(buf, number)
	return buf, nil
}

// una vez agregado el agency y payload se calcula y guarda
// el largo del payload en el header
func AppendBatch(buf []byte, agency byte, payload []byte) ([]byte, error) {
	headerPos := len(buf)
	buf = append(buf, Batch, 0, 0)
	payloadStart := len(buf)

	buf = append(buf, agency)
	buf = append(buf, payload...)

	payloadSize := len(buf) - payloadStart

	if payloadSize > MaxPayloadSize {
		return nil, fmt.Errorf("batch payload de %d bytes excede el maximo de %d", payloadSize, MaxPayloadSize)
	}

	binary.BigEndian.PutUint16(buf[headerPos+1:headerPos+3], uint16(payloadSize))
	return buf, nil
}

func newMessage(tipo byte, payloadSize int) []byte {
	message := make([]byte, headerSize+payloadSize)
	message[0] = tipo
	binary.BigEndian.PutUint16(message[1:3], uint16(payloadSize))
	return message
}

// saca los guiones de "AA-MM-DD" y valida que queden 8 numeros
func encodeBirthdate(birthdate []byte) (uint32, error) {
	var numbers [8]byte
	n := 0
	for _, b := range birthdate {
		if b == '-' {
			continue
		}
		if n >= len(numbers) {
			return 0, fmt.Errorf("fecha de nacimiento invalida: se esperaban 8 digitos (AAAAMMDD), se recibio %q", birthdate)
		}
		numbers[n] = b
		n++
	}
	if n != len(numbers) {
		return 0, fmt.Errorf("fecha de nacimiento invalida: se esperaban 8 digitos (AAAAMMDD), se recibio %q", birthdate)
	}

	value, err := strconv.ParseUint(string(numbers[:]), 10, 32)
	if err != nil {
		return 0, fmt.Errorf("fecha de nacimiento invalida: %w", err)
	}
	return uint32(value), nil
}

// decodificamos el payload de un mensaje winner
// pos a pos, como hay campos de largos dinamicos que estan
// precedidos de un largo de tamaño fijo que lo define
func DecodeWinner(payload []byte) (WinnerMessage, error) {
	name, pos := readFixedField(payload, 0)
	lastname, pos := readFixedField(payload, pos)

	documentBytes := payload[pos : pos+4]
	pos += 4
	document := binary.BigEndian.Uint32(documentBytes)

	birthdateBytes := payload[pos : pos+4]
	pos += 4
	birthdate, err := decodeBirthdate(birthdateBytes)
	if err != nil {
		return WinnerMessage{}, fmt.Errorf("birthdate: %w", err)
	}

	numberBytes := payload[pos : pos+4]
	number := binary.BigEndian.Uint32(numberBytes)

	return WinnerMessage{name, lastname, document, birthdate, number}, nil
}

// inverso de encodeBirthday
func decodeBirthdate(birthdayBytes []byte) (string, error) {
	value := binary.BigEndian.Uint32(birthdayBytes)
	str := strconv.FormatUint(uint64(value), 10)
	if len(str) != 8 {
		return "", fmt.Errorf("fecha de nacimiento invalida: se esperaban 8 digitos (AAAAMMDD), se recibio %q", str)
	}
	return str[0:4] + "-" + str[4:6] + "-" + str[6:8], nil
}

// para los campos de largo variable, codificamos el
// largo definido primero -> el prefijo del byte limita el
// largo posible del campo variable
func appendFixedField(buf []byte, value []byte) ([]byte, error) {
	if len(value) > MaxFieldLength {
		return nil, fmt.Errorf("campo de  %d bytes excede el maximo de %d", len(value), MaxFieldLength)
	}
	buf = append(buf, byte(len(value)))
	buf = append(buf, value...)
	return buf, nil
}

// apra los campos de largo variable, leemos primero el largo
// y despues es cantidad de contenido
func readFixedField(payload []byte, pos int) (string, int) {
	length := int(payload[pos])
	pos++

	value := payload[pos : pos+length]
	pos += length
	return string(value), pos
}
