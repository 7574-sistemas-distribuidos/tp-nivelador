package client

import (
	"bufio"
	"encoding/csv"
	"fmt"
	"net"
	"os"
	"strconv"
	"time"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/business"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/protocol"
)

const CONNECTION_ATTEMPTS_MAX = 3
const CONNECTION_ATTEMPS_DELAY_MS = 200

type ClientConfig struct {
	ServerHost string
	ServerPort string
	AgencyId   int
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
	const action = "run-client"
	defer client.conn.Close()

	inputFile, err := os.Open(client.config.InputFile)
	if err != nil {
		logger.Error("open-input-file", logger.Fail, "err", err)
		return err
	}
	defer inputFile.Close()

	outputFile, err := os.Create(client.config.OutputFile)
	if err != nil {
		logger.Error("create-output-file", logger.Fail, "err", err)
		return err
	}
	defer outputFile.Close()

	channel := protocol.NewMessageChannel(client.conn)

	if err := client.sendBets(channel, inputFile); err != nil {
		return err
	}

	if err := client.receiveBetWinners(channel, outputFile); err != nil {
		return err
	}

	logger.Info(action, logger.Success, "agency-id", client.config.AgencyId)
	return nil
}

func (client *Client) sendBets(channel *protocol.MessageChannel, inputFile *os.File) error {
	const action = "send-bets"
	logger.Info(action, logger.InProgress, "agency-id", client.config.AgencyId)

	startBetsSendingMessage, err := protocol.NewStartBetsSendingMessageFrom(client.config.AgencyId)
	if err != nil {
		logger.Error(action, logger.Fail, "err", err)
		return err
	}
	if err := channel.Send(startBetsSendingMessage); err != nil {
		logger.Error(action, logger.Fail, "err", err)
		return err
	}

	betsSent := 0
	scanner := bufio.NewScanner(inputFile)
	for scanner.Scan() {
		bet, err := business.BetFromLine(scanner.Text())
		if err != nil {
			logger.Error(action, logger.Fail, "bet-line", betsSent+1, "err", err)
			return err
		}

		filledBet, err := protocol.NewFilledBetMessageFrom(bet)
		if err != nil {
			logger.Error(action, logger.Fail, "bet-line", betsSent+1, "err", err)
			return err
		}

		if err := channel.Send(filledBet); err != nil {
			logger.Error(action, logger.Fail, "bet-line", betsSent+1, "err", err)
			return err
		}
		betsSent++
	}
	if err := scanner.Err(); err != nil {
		logger.Error(action, logger.Fail, "err", err)
		return err
	}

	if err := channel.Send(&protocol.FinalizeBetsSendingMessage{}); err != nil {
		logger.Error(action, logger.Fail, "err", err)
		return err
	}

	logger.Info(action, logger.Success, "agency-id", client.config.AgencyId, "bets-sent", betsSent)
	return nil
}

func (client *Client) receiveBetWinners(channel *protocol.MessageChannel, outputFile *os.File) error {
	const action = "receive-bet-winners"
	logger.Info(action, logger.InProgress, "agency-id", client.config.AgencyId)

	firstMessage, err := channel.Receive()
	if err != nil {
		logger.Error(action, logger.Fail, "err", err)
		return err
	}
	if _, isStart := firstMessage.(*protocol.StartBetWinnersSendingMessage); !isStart {
		err := fmt.Errorf("expected a start_bet_winners_sending, got %T", firstMessage)
		logger.Error(action, logger.Fail, "err", err)
		return err
	}

	writer := csv.NewWriter(outputFile)
	winnersReceived := 0
	for {
		message, err := channel.Receive()
		if err != nil {
			logger.Error(action, logger.Fail, "err", err)
			return err
		}

		switch received := message.(type) {
		case *protocol.BetWinnerMessage:
			if err := writer.Write(betWinnerRow(received.Bet())); err != nil {
				logger.Error(action, logger.Fail, "err", err)
				return err
			}
			winnersReceived++
		case *protocol.FinalizeBetWinnersSendingMessage:
			writer.Flush()
			if err := writer.Error(); err != nil {
				logger.Error("write-output-file", logger.Fail, "err", err)
				return err
			}
			logger.Info(
				action, logger.Success,
				"agency-id", client.config.AgencyId, "winners-received", winnersReceived,
			)
			return nil
		default:
			err := fmt.Errorf(
				"expected a bet_winner or a finalize_bet_winners_sending, got %T", received,
			)
			logger.Error(action, logger.Fail, "err", err)
			return err
		}
	}
}

func betWinnerRow(bet business.Bet) []string {
	return []string{
		bet.FirstName,
		bet.LastName,
		strconv.Itoa(bet.Document),
		bet.Birthdate,
		strconv.Itoa(bet.Number),
	}
}
