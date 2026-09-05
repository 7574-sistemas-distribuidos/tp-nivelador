package client

import (
	"bufio"
	"encoding/csv"
	"errors"
	"fmt"
	"net"
	"os"
	"time"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/domain"
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

	sendBetsErr := client.sendBets(inputFile)
	if sendBetsErr != nil {
		return sendBetsErr
	}

	awaitingWinnersErr := client.sendAwaitingWinners()
	if awaitingWinnersErr != nil {
		return awaitingWinnersErr
	}

	winners, winnersErr := client.readWinners()
	if winnersErr != nil {
		return winnersErr
	}

	if storeErr := client.storeWinners(outputFile, winners); storeErr != nil {
		return storeErr
	}

	logger.Info(mainAction, logger.Success, "agency-id", client.config.AgencyId)

	return nil
}

func (client *Client) readInputFile() (*os.File, error) {
	const action = "open-input-file"
	const inputFileArg = "input-file"

	file, err := os.Open(client.config.InputFile)
	if err != nil {
		logger.Error(action, logger.Fail, inputFileArg, client.config.InputFile)
		return nil, err
	}

	logger.Info(action, logger.Success, inputFileArg, client.config.InputFile)
	return file, nil
}

func (client *Client) createOutputFile() (*os.File, error) {
	const action = "create-output-file"
	const outputFileArg = "output-file"

	outputFile, err := os.Create(client.config.OutputFile)
	if err != nil {
		logger.Error(action, logger.Fail, outputFileArg, client.config.OutputFile)
		return nil, err
	}

	logger.Info(action, logger.Success, outputFileArg, client.config.OutputFile)
	return outputFile, nil
}

func (client *Client) sendBets(file *os.File) error {
	scanner := bufio.NewScanner(file)
	scanner.Buffer(make([]byte, BUFFER_SIZE), MAX_LINE_SIZE)

	for messageId := 1; scanner.Scan(); messageId++ {
		bet, betParseErr := domain.ParseBetLine(scanner.Text())
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

func (client *Client) sendBet(bet domain.Bet, betId int) error {
	return client.step("send-bet", func() error {
		message := domain.BetMessage(client.config.AgencyId, bet)
		if err := protocol.SendMessage(client.conn, message); err != nil {
			return err
		}
		return client.readAck()
	}, "bet-id", betId)
}

func (client *Client) sendAwaitingWinners() error {
	return client.step("send-awaiting-winners", func() error {
		message := domain.AwaitingWinnersMessage(client.config.AgencyId)
		if err := protocol.SendMessage(client.conn, message); err != nil {
			return err
		}
		return client.readAck()
	}, "agency-id", client.config.AgencyId)
}

func (client *Client) sendAck() error {
	return protocol.SendMessage(client.conn, domain.AckMessage())
}

func (client *Client) readAck() error {
	return client.step("read-ack", func() error {
		header, _, err := protocol.ReceiveMessage(client.conn)
		if err != nil {
			return err
		}
		if header.Type != domain.MessageTypeAck {
			return errors.New("expected ack message type, got different type")
		}
		return nil
	})
}

func (client *Client) readWinners() ([]domain.Bet, error) {
	var winners []domain.Bet

	err := client.step("read-winners", func() error {
		for {
			header, payload, err := protocol.ReceiveMessage(client.conn)
			if err != nil {
				return err
			}

			switch header.Type {
			case domain.MessageTypeWinner:
				bet, betErr := domain.ParseBetLine(string(payload))
				if betErr != nil {
					return betErr
				}
				winners = append(winners, bet)

				if ackErr := client.sendAck(); ackErr != nil {
					return ackErr
				}
			case domain.MessageTypeFinish:
				// Se confirma el cierre para que el server no corte sobre un socket a medio leer.
				return client.sendAck()
			default:
				return fmt.Errorf("unexpected message type while reading winners: %d", header.Type)
			}
		}
	}, "agency-id", client.config.AgencyId)

	// Ante un error el stream quedo incompleto: se descartan las parciales.
	if err != nil {
		return nil, err
	}
	return winners, nil
}

func (client *Client) storeWinners(file *os.File, winners []domain.Bet) error {
	return client.step("store-winners", func() error {
		rows := make([][]string, 0, len(winners))
		for _, winner := range winners {
			rows = append(rows, winner.Fields())
		}

		// WriteAll hace el Flush y devuelve el error de escritura.
		return csv.NewWriter(file).WriteAll(rows)
	}, "winners-amount", len(winners))
}

func (client *Client) step(action string, fn func() error, args ...any) error {
	logger.Info(action, logger.InProgress, args...)
	if err := fn(); err != nil {
		logger.Error(action, logger.Fail, args...)
		return err
	}
	logger.Info(action, logger.Success, args...)
	return nil
}
