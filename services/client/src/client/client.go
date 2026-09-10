package client

import (
	"context"
	"encoding/binary"
	"fmt"
	"net"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/entities"
	filehandler "github.com/7574-sistemas-distribuidos/tp-nivelador/src/file-handler"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/protocol"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

const CONNECTION_ATTEMPTS_MAX = 3
const CONNECTION_ATTEMPS_DELAY_MS = 1000

const ECHO_CLIENT_MESSAGE_DELAY_MS = 1000

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
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer stop()

	defer func() {
		if client.conn != nil {
			_ = client.conn.Close()
		}
	}()

	go func() {
		<-ctx.Done()
		logger.Warn("client-signal", logger.InProgress, "msg", "SIGTERM received, closing network resources")
		if client.conn != nil {
			_ = client.conn.Close()
		}
	}()

	packetSize, err := strconv.Atoi(client.config.BatchSize)
	thereArePacketsToSend := true
	reader, err := filehandler.NewCSVReader(client.config.InputFilePath)
	if err != nil {
		if ctx.Err() != nil {
			return nil
		}
		logger.Error("read-csv-file", logger.Fail, "err", err)
		return err
	}
	defer reader.Close()

	for thereArePacketsToSend {
		if ctx.Err() != nil {
			return nil
		}

		records, hasMoreRecords, err := reader.ReadBatch(packetSize)
		if err != nil {
			if ctx.Err() != nil {
				return nil
			}
			logger.Error("read-batch", logger.Fail, "err", err)
			return err
		}

		if len(records) > 0 {
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
				if ctx.Err() != nil {
					return nil
				}
				logger.Error("send-packet", logger.Fail, "err", err)
				return err
			}

			ack, err := safe_socket.RecvAll(client.conn, 1)
			if err != nil {
				if ctx.Err() != nil {
					return nil
				}
				logger.Error("recv-ack", logger.Fail, "err", err)
				return err
			}
			if len(ack) != 1 || ack[0] != byte(protocol.AckBetMessage) {
				err = fmt.Errorf("expected AckBetMessage, received %v", ack)
				logger.Error("recv-ack", logger.Fail, "err", err)
				return err
			}
		}

		thereArePacketsToSend = hasMoreRecords
	}

	if ctx.Err() != nil {
		return nil
	}

	allBetsSentPacket, err := protocol.GenerateAllBetsSentPacket(client.config.AgencyId)
	if err != nil {
		logger.Error("generate-all-bets-sent-packet", logger.Fail, "err", err)
		return err
	}
	if err := safe_socket.SendAll(client.conn, allBetsSentPacket); err != nil {
		if ctx.Err() != nil {
			return nil
		}
		logger.Error("send-all-bets-sent-packet", logger.Fail, "err", err)
		return err
	}
	response, err := safe_socket.RecvAll(client.conn, 1)
	if err != nil {
		if ctx.Err() != nil {
			return nil
		}
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
		if ctx.Err() != nil {
			return nil
		}
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
		if ctx.Err() != nil {
			return nil
		}
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
		record := entities.BetToRecord(winner)
		records = append(records, record)
	}
	outputFilePath := client.config.OutputDir

	if ctx.Err() != nil {
		return nil
	}
	werr := filehandler.WriteCSVFile(outputFilePath, records)
	if werr != nil {
		logger.Error("create-csv-writer", logger.Fail, "err", err)
		return err
	}

	return nil
}
