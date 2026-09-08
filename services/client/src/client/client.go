package client

import (
	"net"
	"time"
	"bufio"
	"os"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/protocol"
)

const CONNECTION_ATTEMPTS_MAX = 3
const CONNECTION_ATTEMPS_DELAY_MS = 1000 // 200

const INPUT_FILE = "/app/input/input-"
const OUTPUT_FILE = "/app/output/output-"
const FILE_EXTENSION = ".csv"

type ClientConfig struct {
	ServerHost string
	ServerPort string
	AgencyId   string
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
	const mainAction = "test-echo-server"
	defer client.conn.Close()

	inputFile, err := os.Open(INPUT_FILE + client.config.AgencyId + FILE_EXTENSION)
	if err != nil {
		logger.Error(mainAction, logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}
	defer inputFile.Close()

	outputFile, err := os.Create(OUTPUT_FILE + client.config.AgencyId + FILE_EXTENSION)
	if err != nil {
		logger.Error(mainAction, logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}
	defer outputFile.Close()

	// ENVIO EL AGENCY-ID
	logger.Info(mainAction, logger.Success, "Sending AGENCY-ID: ", client.config.AgencyId)

	if err := protocol.SendInit(client.conn, []byte(client.config.AgencyId)); err != nil {
		logger.Error("send-request", logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}

		// Envio todas las apuestas
	lineCount := 0
	scanner := bufio.NewScanner(inputFile)
	for scanner.Scan() {
		line := scanner.Text()
		lineCount++

		if line == "" {
			continue
		}

		logger.Info(mainAction, logger.Success, "Sending REQUEST: cant-bytes: ", len(line))

		if err := protocol.SendRequest(client.conn, []byte(line)); err != nil {
			logger.Error("send-request", logger.Fail, "agency-id", client.config.AgencyId)
			return err
		}
	}

	logger.Info(mainAction, logger.Success,"Sending EOF")
	if err := protocol.SendEOF(client.conn); err != nil {
		logger.Error("send-eof", logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}

			// Espero por la rspuesta del server de los winners
	winners, err := protocol.ReceiveFrom(client.conn)
	if err != nil {
		logger.Error("receive-response", logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}

	if _, err := outputFile.WriteString(string(winners.Payload())); err != nil {
		logger.Error("write-output-file", logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}

	if err := scanner.Err(); err != nil {
		logger.Error("scan-input-file", logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}
	logger.Info(mainAction, logger.Success, "agency-id", client.config.AgencyId, "lines-read", lineCount)
	

	return nil
}