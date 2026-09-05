package protocol

import (
	"net"
	"strconv"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/entities"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

func SendMessages(conn net.Conn, records [][]string, agencyId string) ([][]string, error) {
	agencyIdParsed, err := strconv.ParseUint(agencyId, 10, 8)

	if err != nil {
		logger.Error("SendMessages", logger.Fail, " Failed to parse AgencyId: ", err)
		return nil, err
	}
	agencyIdBytes := uint8(agencyIdParsed)

	for i, record := range records {
		logger.Info("record", logger.Success, "agency-id", agencyId, "record-id", i, "record", record)
		play, err := entities.NewBetFromRecord(record)
		if err != nil {
			logger.Error("new-play-from-record", logger.Fail, "agency-id", agencyId, "record-id", i, "err", err)
			return nil, err
		}
		playSerialized, err := entities.SerializeBet(play, agencyIdBytes)
		if err != nil {
			logger.Error("serialize-play", logger.Fail, "agency-id", agencyId, "record-id", i, "err", err)
			return nil, err
		}
		betMessage := append([]byte{byte(BetMessage)}, playSerialized...)

		if err := safe_socket.SendAll(conn, betMessage); err != nil {
			logger.Error("send-message", logger.Fail, "agency-id", agencyId, "record-id", i)
			return nil, err
		}

		responseBuffer, err := ReceiveMessage(conn)
		if err != nil {
			logger.Error("recv-response", logger.Fail)
			return nil, err
		}
		logger.Info("record-response", logger.Success, "agency-id", agencyId, "record-id", i, "response", string(responseBuffer))
	}
	logger.Info("send-messages", logger.Success, "agency-id", agencyId, "records-sent", len(records))
	allbBetsMessage := []byte{byte(AllBetsSentMessage), agencyIdBytes}
	if err := safe_socket.SendAll(conn, allbBetsMessage); err != nil {
		logger.Error("send-all-bets-message", logger.Fail, "agency-id", agencyId)
		return nil, err
	}
	logger.Info("send-all-bets-message", logger.Success, "agency-id", agencyId)
	responseBuffer, err := ReceiveMessage(conn)

	winners, err := entities.DeserializeWinner(responseBuffer)
	if err != nil {
		return nil, err
	}
	winnerRecord := entities.WinnerToRecord(winners)
	logger.Info("all-bets-response", logger.Success, "agency-id", agencyId, "response", string(responseBuffer))
	var winnerRecords [][]string
	winnerRecords = append(winnerRecords, winnerRecord)
	return winnerRecords, nil
}
