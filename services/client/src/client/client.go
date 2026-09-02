package client

import (
	"bufio"
	"errors"
	"net"
	"os"
	"time"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/protocol"
)

const CONNECTION_ATTEMPTS_MAX = 3
const CONNECTION_ATTEMPS_DELAY_MS = 200

const BUFFER_SIZE = 512
const MAX_LINE_SIZE = 64 * 1024

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
	const mainAction = "lottery-round"
	defer client.conn.Close()

	logger.Info(mainAction, logger.InProgress, "agency-id", client.config.AgencyId)

	inputFile, fileErr := client.readInputFile()
	if fileErr != nil {
		return fileErr
	}
	defer inputFile.Close()

	outputFile, oFileErr := client.createOutputFile()
	if oFileErr != nil {
		return oFileErr
	}
	defer outputFile.Close()

	registerErr := client.registerAgency(client.config.AgencyId)
	if registerErr != nil {
		return registerErr
	}

	sendBetsErr := client.sendBets(inputFile)
	if sendBetsErr != nil {
		return sendBetsErr
	}

	err := client.readWinners(outputFile)
	if err != nil {
		return err
	}

	logger.Info(mainAction, logger.Success, "agency-id", client.config.AgencyId)

	return nil
}

func (client *Client) readInputFile() (*os.File, error) {
	file, err := os.Open(client.config.InputFile)
	if err != nil {
		logger.Warn("open-file", logger.Fail, "input-file", client.config.InputFile)
		return nil, err
	}
	return file, nil
}

func (client *Client) createOutputFile() (*os.File, error) {
	outputFile, err := os.Create(client.config.OutputFile)
	if err != nil {
		logger.Warn("create-output-file", logger.Fail, "output-file", client.config.OutputFile)
		return nil, err
	}
	return outputFile, nil
}

func (client *Client) registerAgency(agencyId string) error {
	payload := []byte(agencyId)
	if err := protocol.SendMessage(client.conn, protocol.MessageTypeRegisterAgency, payload); err != nil {
		logger.Error("register-agency", logger.Fail, "agency-id", agencyId)
		return err
	}
	if err := client.readAck(); err != nil {
		return err
	}
	return nil
}

func (client *Client) sendBets(file *os.File) error {
	scanner := bufio.NewScanner(file)
	scanner.Buffer(make([]byte, BUFFER_SIZE), MAX_LINE_SIZE)

	for messageId := 1; scanner.Scan(); messageId++ {
		bet, betParseErr := protocol.ParseBetLine(scanner.Text())
		if betParseErr != nil {
			return betParseErr
		}
		sendBetErr := client.sendBet(bet, messageId)
		if sendBetErr != nil {
			return sendBetErr
		}
	}

	if err := scanner.Err(); err != nil {
		logger.Error("read-file", logger.Fail, "input-file", client.config.InputFile)
		return err
	}
	return nil
}

func (client *Client) readWinners(outputFile *os.File) error {
	output := bufio.NewWriter(outputFile)

	if err := output.Flush(); err != nil {
		logger.Error("write-output-file", logger.Fail, "output-file", client.config.OutputFile)
		return err
	}
	return nil
}

func (client *Client) sendBet(bet protocol.Bet, betId int) error {
	logger.Info("send-bet", logger.InProgress, "bet-id", betId)

	payload := bet.Serialize()
	if err := protocol.SendMessage(client.conn, protocol.MessageTypeBet, payload); err != nil {
		logger.Error("send-bet-message", logger.Fail, "bet", string(payload))
		return err
	}

	err2 := client.readAck()
	if err2 != nil {
		return err2
	}
	return nil
}

func (client *Client) readAck() error {
	header, _, err := protocol.ReceiveMessage(client.conn)
	if err != nil {
		logger.Error("read-ack", logger.Fail)
		return err
	}
	if header.Type != protocol.MessageTypeAck {
		logger.Error("invalid-message-type", logger.Fail)
		return errors.New("expected ack message type, got different type")
	}
	return nil
}
