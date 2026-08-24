package client

import (
	"bufio"
	"errors"
	"net"
	"os"
	"time"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

const ConnectionAttemptsMax = 3
const ConnectionAttempsDelayMs = 200

type Config struct {
	ServerHost string
	ServerPort string
	AgencyId   string
	InputFile  string
	OutputFile string
}

type Client struct {
	conn   net.Conn
	config Config
}

func NewClient(config Config) (*Client, error) {
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

	for i := range ConnectionAttemptsMax {
		conn, err = net.Dial("tcp", host+":"+port)

		if err != nil {
			logger.Warn(action, logger.Fail, "attempt", i)
			time.Sleep(ConnectionAttempsDelayMs * time.Millisecond)
			continue
		}
		logger.Info(action, logger.Success)
		break
	}
	return conn, err
}

func (client *Client) closeConnection(err *error) {
	if closeConnectionError := client.conn.Close(); closeConnectionError != nil {
		logger.Error("close-connection", logger.Fail)
		*err = errors.Join(*err, closeConnectionError)
	}
}

func (client *Client) closeFile(file *os.File, err *error) {
	if closeError := file.Close(); closeError != nil {
		logger.Error("close-input-file", logger.Fail, "path", file.Name())
		*err = errors.Join(*err, closeError)
	}
}

func (client *Client) flushFile(writer *bufio.Writer, err *error) {
	if flushError := writer.Flush(); flushError != nil {
		logger.Error("flush-output-file", logger.Fail)
		*err = errors.Join(*err, flushError)
	}
}

func (client *Client) Run() (err error) {
	const mainAction = "send-input-file"
	defer client.closeConnection(&err)

	inputFile, err := os.Open(client.config.InputFile)

	if err != nil {
		logger.Error("open-input-file", logger.Fail, "path", client.config.InputFile)
		return err
	}
	defer client.closeFile(inputFile, &err)

	outputFile, err := os.Create(client.config.OutputFile)

	if err != nil {
		logger.Error("open-output-file", logger.Fail, "path", client.config.OutputFile)
		return err
	}
	defer client.closeFile(outputFile, &err)

	scanner := bufio.NewScanner(inputFile)
	writer := bufio.NewWriter(outputFile)

	defer client.flushFile(writer, &err)

	logger.Info(mainAction, logger.InProgress)
	var messageId uint

	for messageId := 0; scanner.Scan(); messageId++ {
		clientMessage := scanner.Text()
		messageArgs := []any{"message", clientMessage, "message-id", messageId}

		if err := safe_socket.SendAll(client.conn, []byte(clientMessage)); err != nil {
			logger.Error("send-message", logger.Fail, messageArgs...)
			return err
		}
		responseBuffer, err := safe_socket.RecvAll(client.conn, len(clientMessage))

		if err != nil {
			logger.Error("recv-response", logger.Fail, messageArgs...)
			return err
		}
		if string(responseBuffer) != clientMessage {
			logger.Error("check-response", logger.Fail, messageArgs...)
			return err
		}
		responseBuffer = append(responseBuffer, '\n')

		if _, err := writer.Write(responseBuffer); err != nil {
			logger.Error("write-file", logger.Fail, messageArgs...)
			return err
		}
	}
	logger.Info(mainAction, logger.Success, "input-file", client.config.InputFile, "messages-amount", messageId)
	return nil
}
