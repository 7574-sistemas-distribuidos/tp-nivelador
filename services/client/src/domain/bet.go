package domain

import (
	"fmt"
	"strings"
)

const BET_FIELDS_AMOUNT = 5

// Representa una apuesta tal como viene en el archivo de entrada. Ejemplo:
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
	if len(fields) != BET_FIELDS_AMOUNT {
		return Bet{}, fmt.Errorf("invalid bet payload: expected %d fields, got %d", BET_FIELDS_AMOUNT, len(fields))
	}
	return Bet{
		fields[0],
		fields[1],
		fields[2],
		fields[3],
		fields[4],
	}, nil
}

// Campos en el orden del archivo de entrada.
func (b Bet) Fields() []string {
	return []string{b.FirstName, b.LastName, b.Document, b.BirthDate, b.Number}
}

func (b Bet) Serialize(agencyId string) []byte {
	fields := append([]string{agencyId}, b.Fields()...)
	return []byte(strings.Join(fields, ","))
}
