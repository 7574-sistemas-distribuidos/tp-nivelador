package protocol

import (
	"fmt"
	"strings"
)

// Representa una apuesta. Ejemplo:
// Santiago Lionel,Lorca,30904465,1999-03-17,7574\n
type Bet struct {
	FirstName string
	LastName  string
	Document  string
	BirthDate string
	Number    string
}

func ParseBetLine(line string) (Bet, error) {
	line = strings.Replace(line, "\n", "", -1)
	fields := strings.Split(line, ",")
	if len(fields) != 5 {
		return Bet{}, fmt.Errorf("invalid bet payload: expected 5 fields, got %d", len(fields))
	}
	return Bet{
		fields[0],
		fields[1],
		fields[2],
		fields[3],
		fields[4],
	}, nil
}

func (b Bet) Serialize() []byte {
	fields := []string{b.FirstName, b.LastName, b.Document, b.BirthDate, b.Number}
	return []byte(strings.Join(fields, ","))
}
