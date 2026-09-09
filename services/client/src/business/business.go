package business

import (
	"fmt"
	"strconv"
	"strings"
)

type Bet struct {
	Document  int
	Number    int
	Birthdate string
	FirstName string
	LastName  string
}

func BetFromLine(line string) (Bet, error) {
	fields := strings.Split(line, ",")

	document, _ := strconv.Atoi(fields[2])
	if document < 0 {
		return Bet{}, fmt.Errorf("document must not be negative, got %d", document)
	}

	number, _ := strconv.Atoi(fields[4])
	if number < 0 {
		return Bet{}, fmt.Errorf("number must not be negative, got %d", number)
	}

	return Bet{
		Document:  document,
		Number:    number,
		Birthdate: fields[3],
		FirstName: fields[0],
		LastName:  fields[1],
	}, nil
}
