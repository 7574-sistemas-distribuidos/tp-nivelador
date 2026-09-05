package client

import (
	"net"
	"time"

	filehandler "github.com/7574-sistemas-distribuidos/tp-nivelador/src/file-handler"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/protocol"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

const CONNECTION_ATTEMPTS_MAX = 3
const CONNECTION_ATTEMPS_DELAY_MS = 500

const ECHO_CLIENT_BUFFER_SIZE = 1
const ECHO_CLIENT_MESSAGE_AMOUNT = 3
const ECHO_CLIENT_MESSAGE_DELAY_MS = 1000

type ClientConfig struct {
	ServerHost    string
	ServerPort    string
	AgencyId      string
	InputFilePath string
	OutputDir     string
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

func (client *Client) test_echo_server() error {
	const mainAction = "test-echo-server"
	defer client.conn.Close()

	for messageId := range ECHO_CLIENT_MESSAGE_AMOUNT {
		messageArgs := []any{"agency-id", client.config.AgencyId, "message-id", messageId}
		logger.Info(mainAction, logger.InProgress, messageArgs...)

		clientMessage := client.config.AgencyId

		if err := safe_socket.SendAll(client.conn, []byte(clientMessage)); err != nil {
			logger.Error("send-message", logger.Fail, messageArgs...)
			return err
		}

		responseBuffer, err := safe_socket.RecvAll(client.conn, ECHO_CLIENT_BUFFER_SIZE)
		if err != nil {
			logger.Error("recv-response", logger.Fail, messageArgs...)
			return err
		}
		logger.Info("response", logger.Success, "agency-id", client.config.AgencyId, "response", string(responseBuffer))
		logger.Info("check-response", logger.InProgress, clientMessage)

		if string(responseBuffer) != clientMessage {
			logger.Error("check-response", logger.Fail, messageArgs...)
			return err
		}

		time.Sleep(ECHO_CLIENT_MESSAGE_DELAY_MS * time.Millisecond)
	}
	return nil
}

func (client *Client) Run() error {
	const mainAction = "run-client"
	records, err := filehandler.ReadCSVFile(client.config.InputFilePath)
	if err != nil {
		logger.Error("read-csv-file", logger.Fail, "err", err)
		return err
	}
	recordAmount := len(records)
	logger.Info("read-csv-file", logger.Success, "records", recordAmount)
	receivedRecords, err := protocol.SendMessages(client.conn, records, client.config.AgencyId)
	if err != nil {
		logger.Error("send-messages", logger.Fail, "err", err)
		return err
	}
	if err := filehandler.WriteCSVFile(client.config.OutputDir+"/output-"+client.config.AgencyId+".csv", receivedRecords); err != nil {
		logger.Error("write-csv-file", logger.Fail, "err", err)
		return err
	}

	return nil
}
