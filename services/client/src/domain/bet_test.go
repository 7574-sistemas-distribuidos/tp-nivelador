package domain

import (
	"testing"
)

func TestCanParseBetFromCSVLine(t *testing.T) {
	line := "Santiago Lionel,Lorca,30904465,1999-03-17,7574\n"

	bet, err := ParseBetLine(line)

	if err != nil {
		t.Fatalf("can_parse_bet_from_csv_line: expected no error, got %v", err)
	}

	expected := Bet{
		FirstName: "Santiago Lionel",
		LastName:  "Lorca",
		Document:  "30904465",
		BirthDate: "1999-03-17",
		Number:    "7574",
	}

	if bet != expected {
		t.Fatalf("can_parse_bet_from_csv_line: expected %+v, got %+v", expected, bet)
	}
}

func TestSerializeBetPrependsAgencyId(t *testing.T) {
	bet := Bet{
		FirstName: "Santiago Lionel",
		LastName:  "Lorca",
		Document:  "30904465",
		BirthDate: "1999-03-17",
		Number:    "7574",
	}

	serialized := string(bet.Serialize("1"))

	expected := "1,Santiago Lionel,Lorca,30904465,1999-03-17,7574"
	if serialized != expected {
		t.Fatalf("serialize_bet_prepends_agency_id: expected %q, got %q", expected, serialized)
	}
}
