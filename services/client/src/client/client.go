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

const CONNECTION_ATTEMPTS_MAX = 3
const CONNECTION_ATTEMPS_DELAY_MS = 200

type ClientConfig struct {
	ServerHost string
	ServerPort string
	AgencyId   string
	InputFile  string
	OutputFile string
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
	for scanner.Scan() {
		line := scanner.Text()
		if len(strings.TrimSpace(line)) == 0 {
			continue
		}
		lineCount++

		payload := []byte(client.config.AgencyId + "," + line)
		if err := protocol.SendMsg(client.conn, protocol.MsgBet, payload); err != nil {
			logger.Error("send-bet", logger.Fail, "agency-id", client.config.AgencyId, "line", lineCount, "err", err)
			return err
		}

		msgType, _, err := protocol.RecvMsg(client.conn)
		if err != nil {
			logger.Error("recv-ack", logger.Fail, "agency-id", client.config.AgencyId, "line", lineCount, "err", err)
			return err
		}
		if msgType != protocol.MsgAck {
			logger.Error("check-ack", logger.Fail, "agency-id", client.config.AgencyId, "expected", protocol.MsgAck, "got", msgType)
			return fmt.Errorf("unexpected message type: %d", msgType)
		}
	}

	if err := scanner.Err(); err != nil {
		logger.Error("scan-file", logger.Fail, "agency-id", client.config.AgencyId, "err", err)
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
