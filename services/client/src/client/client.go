package client

import (
	"net"
	"time"
	"bufio"
	"os"
	"encoding/binary"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

const CONNECTION_ATTEMPTS_MAX = 3
const CONNECTION_ATTEMPS_DELAY_MS = 1000 // 200

const ECHO_CLIENT_MESSAGE_AMOUNT = 3
const ECHO_CLIENT_MESSAGE_DELAY_MS = 1000
const INPUT_FILE = "/app/input/input-"
const OUTPUT_FILE = "/app/output/output-"
const FILE_EXTENSION = ".csv"
const LENGTH_MESSAGE_SIZE = 2

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

	lineCount := 0
	scanner := bufio.NewScanner(inputFile)
	for scanner.Scan() {
		line := scanner.Text()
		lineCount++

		length_msg := make([]byte, LENGTH_MESSAGE_SIZE) // revisar numero 
		binary.BigEndian.PutUint16(length_msg, uint16(len(line)))

		if err := safe_socket.SendAll(client.conn, length_msg); err != nil {
			logger.Error("send-message-length", logger.Fail, "agency-id", client.config.AgencyId)
			return err
		}

		messageArgs := []any{"agency-id", client.config.AgencyId, "message", line}
		logger.Info(mainAction, logger.InProgress, messageArgs...)

		if err := safe_socket.SendAll(client.conn, []byte(line)); err != nil {
			logger.Error("send-message", logger.Fail, messageArgs...)
			return err
		}

		length_response, err := safe_socket.RecvAll(client.conn, LENGTH_MESSAGE_SIZE) 
		if err != nil {
			logger.Error("recv-response-length", logger.Fail, messageArgs...)
			return err
		}

		responseSize := int(binary.BigEndian.Uint16(length_response))
		responseBuffer, err := safe_socket.RecvAll(client.conn, responseSize)
		if err != nil {
			logger.Error("recv-response", logger.Fail, messageArgs...)
			return err
		}

		if _, err := outputFile.WriteString(string(responseBuffer) + "\n"); err != nil {
			logger.Error("write-output-file", logger.Fail, messageArgs...)
			return err
		}
	}
	if err := scanner.Err(); err != nil {
		logger.Error("scan-input-file", logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}
	logger.Info(mainAction, logger.Success, "agency-id", client.config.AgencyId, "lines-read", lineCount)
	

	return nil
}