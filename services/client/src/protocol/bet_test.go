package protocol

import "testing"

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
