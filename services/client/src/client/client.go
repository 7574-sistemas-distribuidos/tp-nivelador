package client

import (
	"encoding/binary"
	"net"
	"strconv"
	"time"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/entities"
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
const RETRY_ATTEMPTS_MAX = 3
const RETRY_ATTEMPTS_DELAY_MS = 500

type ClientConfig struct {
	ServerHost    string
	ServerPort    string
	AgencyId      string
	InputFilePath string
	OutputDir     string
	BatchSize     string
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
	const mainAction = "run-client"
	packetSize, err := strconv.Atoi(client.config.BatchSize)
	thereArePacketsToSend := true
	reader, err := filehandler.NewCSVReader(client.config.InputFilePath)
	if err != nil {
		logger.Error("read-csv-file", logger.Fail, "err", err)
		return err
	}
	defer reader.Close()

	for thereArePacketsToSend {

		records, hasMoreRecords, err := reader.ReadBatch(packetSize)
		if err != nil {
			logger.Error("read-batch", logger.Fail, "err", err)
			return err
		}

		bets, err := entities.BetsFromRecords(records)
		if err != nil {
			logger.Error("bets-from-records", logger.Fail, "err", err)
			return err
		}

		betPacket, err := protocol.GenerateBetPacket(bets, client.config.AgencyId)
		if err != nil {
			logger.Error("generate-packets", logger.Fail, "err", err)
			return err
		}
		if err := safe_socket.SendAll(client.conn, betPacket); err != nil {
			logger.Error("send-packet", logger.Fail, "err", err)
			return err
		}

		thereArePacketsToSend = hasMoreRecords
	}
	allBetsSentPacket, err := protocol.GenerateAllBetsSentPacket(client.config.AgencyId)
	if err != nil {
		logger.Error("generate-all-bets-sent-packet", logger.Fail, "err", err)
		return err
	}
	if err := safe_socket.SendAll(client.conn, allBetsSentPacket); err != nil {
		logger.Error("send-all-bets-sent-packet", logger.Fail, "err", err)
		return err
	}
	response, err := safe_socket.RecvAll(client.conn, 1)
	if err != nil {
		logger.Error("recv-response", logger.Fail, "err", err)
		return err
	}
	isWinnerResponse, err := protocol.UnpackMessageType(response)

	if err != nil {
		logger.Error("unpack-response", logger.Fail, "err", err)
		return err
	}
	if !isWinnerResponse {
		logger.Error("unpack-response", logger.Fail, "err", "Expected a WinnersMessage or FinalizeMessage, but received an unexpected message type.")
		return err
	}
	payloadLengthBytes, err := safe_socket.RecvAll(client.conn, 4)
	if err != nil {
		logger.Error("recv-winners-bets-amount", logger.Fail, "err", err)
		return err
	}
	payloadLength, err := binary.BigEndian.Uint32(payloadLengthBytes), nil
	if err != nil {
		logger.Error("unpack-payload-length", logger.Fail, "err", err)
		return err
	}
	logger.Info(mainAction, logger.InProgress, "payload-length", payloadLength)
	payload, err := safe_socket.RecvAll(client.conn, int(payloadLength))
	if err != nil {
		logger.Error("recv-winners-bets-payload", logger.Fail, "err", err)
		return err
	}
	winners, err := protocol.UnpackWinners(payload)
	if err != nil {
		logger.Error("unpack-winners-bets", logger.Fail, "err", err)
		return err
	}
	var records [][]string
	for _, winner := range winners {
		record := entities.WinnerToRecord(winner)
		records = append(records, record)
	}
	outputFilePath := client.config.OutputDir + "/winners-" + client.config.AgencyId + ".csv"
	werr := filehandler.WriteCSVFile(outputFilePath, records)
	if werr != nil {
		logger.Error("create-csv-writer", logger.Fail, "err", err)
		return err
	}

	return nil
}
