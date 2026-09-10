package client

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"strings"
	"time"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/protocol"
)

const CONNECTION_ATTEMPTS_MAX = 10
const CONNECTION_ATTEMPS_DELAY_MS = 500

type ClientConfig struct {
	ServerHost string
	ServerPort string
	AgencyId   string
	InputFile  string
	OutputFile string
	BatchSize  int
}

type Client struct {
	conn   net.Conn
	config ClientConfig
}

func NewClient(config ClientConfig) (*Client, error) {
	conn, err := connectToServer(config.ServerHost, config.ServerPort)
	if err != nil {
		logger.Warn("connect-to-server", logger.Fail)
		return nil, err
	}

	client := &Client{conn: conn, config: config}
	return client, nil
}

func connectToServer(host, port string) (net.Conn, error) {
	const action = "connect-to-server"
	var err error
	var conn net.Conn

	logger.Info(action, logger.InProgress)
	for i := range CONNECTION_ATTEMPTS_MAX {
		conn, err = net.Dial("tcp", host+":"+port)
		if err != nil {
			logger.Warn(action, logger.Fail, "attempt", i)
			time.Sleep(CONNECTION_ATTEMPS_DELAY_MS * time.Millisecond)
			continue
		}

		logger.Info(action, logger.Success)
		break
	}

	return conn, err
}

func (client *Client) Run() error {
	const mainAction = "send-bets"
	defer client.conn.Close()

	inputFile, err := os.Open(client.config.InputFile)
	if err != nil {
		logger.Error("open-input-file", logger.Fail, "err", err, "path", client.config.InputFile)
		return err
	}
	defer inputFile.Close()

	outputFile, err := os.Create(client.config.OutputFile)
	if err != nil {
		logger.Error("create-output-file", logger.Fail, "err", err, "path", client.config.OutputFile)
		return err
	}
	defer outputFile.Close()

	logger.Info(mainAction, logger.InProgress, "agency-id", client.config.AgencyId)

	scanner := bufio.NewScanner(inputFile)
	lineCount := 0
	var batch []string

	sendBatch := func() error {
		if len(batch) == 0 {
			return nil
		}
		payload := []byte(strings.Join(batch, "\n") + "\n")
		if err := protocol.SendMsg(client.conn, protocol.MsgBet, payload); err != nil {
			logger.Error("send-bet-batch", logger.Fail, "agency-id", client.config.AgencyId, "bets", len(batch), "err", err)
			return err
		}

		msgType, _, err := protocol.RecvMsg(client.conn)
		if err != nil {
			logger.Error("recv-ack", logger.Fail, "agency-id", client.config.AgencyId, "err", err)
			return err
		}
		if msgType != protocol.MsgAck {
			logger.Error("check-ack", logger.Fail, "agency-id", client.config.AgencyId, "expected", protocol.MsgAck, "got", msgType)
			return fmt.Errorf("unexpected message type: %d", msgType)
		}

		batch = batch[:0]
		return nil
	}

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if len(line) == 0 {
			continue
		}
		lineCount++
		batch = append(batch, client.config.AgencyId+","+line)

		if len(batch) >= client.config.BatchSize {
			if err := sendBatch(); err != nil {
				return err
			}
		}
	}

	if err := scanner.Err(); err != nil {
		logger.Error("scan-file", logger.Fail, "agency-id", client.config.AgencyId, "err", err)
		return err
	}

	// Enviar remanente del último lote
	if err := sendBatch(); err != nil {
		return err
	}

	// Notificar fin de envío de apuestas y solicitar ganadores
	if err := protocol.SendMsg(client.conn, protocol.MsgEndBets, []byte(client.config.AgencyId)); err != nil {
		logger.Error("send-end-bets", logger.Fail, "agency-id", client.config.AgencyId, "err", err)
		return err
	}

	// Recibir listado de ganadores
	msgType, winnersPayload, err := protocol.RecvMsg(client.conn)
	if err != nil {
		logger.Error("recv-winners", logger.Fail, "agency-id", client.config.AgencyId, "err", err)
		return err
	}
	if msgType != protocol.MsgWinners {
		logger.Error("check-winners", logger.Fail, "agency-id", client.config.AgencyId, "expected", protocol.MsgWinners, "got", msgType)
		return fmt.Errorf("unexpected message type: %d", msgType)
	}

	// Persistir los ganadores en el archivo de salida
	if len(winnersPayload) > 0 {
		if _, err := outputFile.Write(winnersPayload); err != nil {
			logger.Error("write-output", logger.Fail, "agency-id", client.config.AgencyId, "err", err)
			return err
		}
	}

	logger.Info(mainAction, logger.Success, "agency-id", client.config.AgencyId, "total-bets", lineCount)
	return nil
}
