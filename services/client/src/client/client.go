package client

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"time"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

const CONNECTION_ATTEMPTS_MAX = 3
const CONNECTION_ATTEMPS_DELAY_MS = 200

const ECHO_CLIENT_BUFFER_SIZE = 512
const ECHO_CLIENT_MAX_LINE_SIZE = 64 * 1024

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
	const mainAction = "test-echo-server"
	defer client.conn.Close()

	file, err := os.Open(client.config.InputFile)
	if err != nil {
		logger.Warn("open-file", logger.Fail, "input-file", client.config.InputFile)
		return err
	}
	defer file.Close()

	outputFile, err := os.Create(client.config.OutputFile)
	if err != nil {
		logger.Warn("create-output-file", logger.Fail, "output-file", client.config.OutputFile)
		return err
	}
	defer outputFile.Close()
	output := bufio.NewWriter(outputFile)

	scanner := bufio.NewScanner(file)
	scanner.Buffer(make([]byte, ECHO_CLIENT_BUFFER_SIZE), ECHO_CLIENT_MAX_LINE_SIZE)

	for messageId := 1; scanner.Scan(); messageId++ {
		err2 := sendLine(scanner, client, output, messageId, mainAction)
		if err2 != nil {
			return err2
		}
	}

	if err := scanner.Err(); err != nil {
		logger.Error("read-file", logger.Fail, "input-file", client.config.InputFile)
		return err
	}

	if err := output.Flush(); err != nil {
		logger.Error("write-output-file", logger.Fail, "output-file", client.config.OutputFile)
		return err
	}

	logger.Info(mainAction, logger.Success, "agency-id", client.config.AgencyId)

	return nil
}

func sendLine(scanner *bufio.Scanner, client *Client, output *bufio.Writer, messageId int, mainAction string) error {
	line := scanner.Bytes()
	messageArgs := []any{"agency-id", client.config.AgencyId, "message-id", messageId}
	logger.Info(mainAction, logger.InProgress, messageArgs...)

	if err := safe_socket.SendAll(client.conn, line); err != nil {
		logger.Error("send-message", logger.Fail, messageArgs...)
		return err
	}

	responseBuffer, err := safe_socket.RecvAll(client.conn, len(line))
	if err != nil {
		logger.Error("recv-response", logger.Fail, messageArgs...)
		return err
	}

	if string(responseBuffer) != string(line) {
		logger.Error("check-response", logger.Fail, messageArgs...)
		return fmt.Errorf("echo mismatch on message %d", messageId)
	}

	if _, err := output.Write(append(responseBuffer, '\n')); err != nil {
		logger.Error("write-response", logger.Fail, messageArgs...)
		return err
	}

	return nil
}
