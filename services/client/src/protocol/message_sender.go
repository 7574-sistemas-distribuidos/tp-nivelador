package protocol

import (
	"net"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/entities"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

func SendMessages(conn net.Conn, records [][]string, agencyId string) error {
	for i, record := range records {
		logger.Info("record", logger.Success, "agency-id", agencyId, "record-id", i, "record", record)
		play, err := entities.NewBetFromRecord(record)
		if err != nil {
			logger.Error("new-play-from-record", logger.Fail, "agency-id", agencyId, "record-id", i, "err", err)
			return err
		}
		playSerialized, err := entities.SerializeBet(play, agencyId)
		if err != nil {
			logger.Error("serialize-play", logger.Fail, "agency-id", agencyId, "record-id", i, "err", err)
			return err
		}
		betMessage := append([]byte{byte(BetMessage)}, playSerialized...)

		if err := safe_socket.SendAll(conn, betMessage); err != nil {
			logger.Error("send-message", logger.Fail, "agency-id", agencyId, "record-id", i)
			return err
		}

		responseBuffer, err := ReceiveMessage(conn)
		if err != nil {
			logger.Error("recv-response", logger.Fail)
			return err
		}
		logger.Info("record-response", logger.Success, "agency-id", agencyId, "record-id", i, "response", string(responseBuffer))
	}
	logger.Info("send-messages", logger.Success, "agency-id", agencyId, "records-sent", len(records))
	allbBetsMessage := []byte{byte(AllBetsSentMessage)}
	if err := safe_socket.SendAll(conn, allbBetsMessage); err != nil {
		logger.Error("send-all-bets-message", logger.Fail, "agency-id", agencyId)
		return err
	}
	logger.Info("send-all-bets-message", logger.Success, "agency-id", agencyId)
	return nil
}
