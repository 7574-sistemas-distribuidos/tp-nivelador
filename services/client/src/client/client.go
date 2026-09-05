package client

import (
	"context"
	"fmt"
	"io"
	"net"
	"strconv"
	"strings"
	"time"

	"bufio"
	"os"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/protocol"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

const CONNECTION_ATTEMPTS_MAX = 6
const CONNECTION_ATTEMPS_DELAY_MS = 1000

type ClientConfig struct {
	ServerHost string
	ServerPort string
	AgencyId   string
	InputFile  string
	OutputFile string
	BatchSize  string
}

type Client struct {
	conn      net.Conn
	config    ClientConfig
	agency    byte
	batchSize int
	sendBuf   []byte
	ctx       context.Context
}

func NewClient(ctx context.Context, config ClientConfig) (*Client, error) {
	conn, err := connectToServer(ctx, config.ServerHost, config.ServerPort)
	if err != nil {
		logger.Warn("connect-to-server", logger.Fail)
		return nil, err
	}

	agencyId, err := strconv.Atoi(config.AgencyId)
	if err != nil {
		return nil, err
	}

	batchSize, err := strconv.Atoi(config.BatchSize)
	if err != nil {
		return nil, err
	}

	if batchSize < 1 {
		return nil, fmt.Errorf("tamaño de batch invalido: %d", batchSize)
	}

	return &Client{conn: conn, config: config, agency: byte(agencyId), batchSize: batchSize, ctx: ctx}, nil
}

func connectToServer(ctx context.Context, host, port string) (net.Conn, error) {
	const action = "connect-to-server"
	var err error
	var conn net.Conn
	logger.Info(action, logger.InProgress)

	for i := range CONNECTION_ATTEMPTS_MAX {
		conn, err = net.Dial("tcp", host+":"+port)
		if err != nil {
			logger.Warn(action, logger.Fail, "attempt", i)
			select {
			case <-time.After(CONNECTION_ATTEMPS_DELAY_MS * time.Millisecond):
			case <-ctx.Done():
				return nil, ctx.Err()
			}
			continue
		}

		logger.Info(action, logger.Success)
		break
	}

	return conn, err
}

func (client *Client) Run() error {
	defer client.conn.Close()

	go func() {
		<-client.ctx.Done()
		client.conn.Close()
	}()

	if err := client.sendBets(); err != nil {
		logger.Error("send-bets", logger.Fail)
		return err
	}

	if err := safe_socket.SendAll(client.conn, protocol.EncodeEnd()); err != nil {
		logger.Error("send-end", logger.Fail)
		return err
	}

	if err := client.receiveWinners(); err != nil {
		logger.Error("receive-winners", logger.Fail)
		return err
	}

	logger.Info("client-run", logger.Success, "agency-id", client.config.AgencyId)
	return nil
}

func (client *Client) sendBets() error {
	inputFile, err := os.Open(client.config.InputFile)
	if err != nil {
		logger.Error("open-input-file", logger.Fail)
		return err
	}

	defer inputFile.Close()
	reader := bufio.NewReader(inputFile)
	batchBets := 0
	batchBytes := 0
	var batch []byte
	var encodedNewBet []byte

	for {
		line, readErr := reader.ReadString('\n')
		trimmed := strings.TrimRight(line, "\r\n")

		if trimmed != "" {
			bet, err := client.parseRowIntoBet(trimmed)
			if err != nil {
				return err
			}

			encodedNewBet, err = protocol.EncodeBet(encodedNewBet[:0], bet)
			if err != nil {
				return err
			}

			batch, batchBytes, batchBets, err = client.accumulateBatch(batch, batchBets, batchBytes, encodedNewBet)
			if err != nil {
				return err
			}
		}

		if readErr == io.EOF {
			break
		}
		if readErr != nil {
			logger.Error("read-input", logger.Fail)
			return readErr
		}
	}

	if len(batch) > 0 {
		if err := client.SendBatch(batch); err != nil {
			return err
		}
	}
	return nil
}

func (client *Client) accumulateBatch(batch []byte, batchBets int, batchBytes int, encodedNewBet []byte) ([]byte, int, int, error) {
	if batchBets == client.batchSize || batchBytes+len(encodedNewBet) > protocol.MaxPayloadSize {
		if err := client.SendBatch(batch); err != nil {
			return nil, 0, 0, err
		}
		batch = batch[:0]
		batchBytes = 0
		batchBets = 0
	}
	batch = append(batch, encodedNewBet...)
	batchBytes += len(encodedNewBet)
	return batch, batchBytes, batchBets + 1, nil
}

func (client *Client) SendBatch(payload []byte) error {
	sendBuf, err := protocol.AppendBatch(client.sendBuf[:0], payload)
	if err != nil {
		logger.Error("encode-batch", logger.Fail)
		return err
	}

	client.sendBuf = sendBuf

	if err := safe_socket.SendAll(client.conn, client.sendBuf); err != nil {
		logger.Error("send-batch", logger.Fail)
		return err
	}

	msgType, _, err := protocol.ReadMessage(client.conn)
	if err != nil {
		logger.Error("recv-batch-ack", logger.Fail)
		return err
	}
	if msgType != protocol.Ack {
		return fmt.Errorf("mensaje inesperado del servidor: %d", msgType)
	}
	return nil
}

func (client *Client) receiveWinners() error {
	outputFile, err := os.Create(client.config.OutputFile)
	if err != nil {
		logger.Error("create-output-file", logger.Fail)
		return err
	}

	defer outputFile.Close()
	writer := bufio.NewWriter(outputFile)

	for {
		msgType, payload, err := protocol.ReadMessage(client.conn)
		if err != nil {
			logger.Error("recv-message", logger.Fail)
			return err
		}

		if msgType == protocol.End {
			break
		}

		if msgType != protocol.Winner {
			return fmt.Errorf("mensaje inesperado del servidor: %d", msgType)
		}

		winner, err := protocol.DecodeWinner(payload)
		if err != nil {
			logger.Error("decode-winner", logger.Fail)
			return err
		}

		row := []string{
			winner.Name,
			winner.Lastname,
			strconv.FormatUint(uint64(winner.Document), 10),
			winner.Birthdate,
			strconv.FormatUint(uint64(winner.Number), 10),
		}

		if _, err := writer.WriteString(strings.Join(row, ",") + "\n"); err != nil {
			logger.Error("write-output", logger.Fail)
			return err
		}

		if err := writer.Flush(); err != nil {
			logger.Error("flush-output", logger.Fail)
			return err
		}

		if err := safe_socket.SendAll(client.conn, protocol.EncodeAck()); err != nil {
			logger.Error("send-winner-ack", logger.Fail)
			return err
		}
	}

	return nil
}

func (client *Client) parseRowIntoBet(trimmed string) (protocol.BetMessage, error) {
	row := strings.Split(trimmed, ",")
	if len(row) != 5 {
		return protocol.BetMessage{}, fmt.Errorf("línea invalida, se esperaban 5 campos y se encontraron %d: %q", len(row), trimmed)
	}

	documento, err := strconv.ParseUint(row[2], 10, 32)
	if err != nil {
		return protocol.BetMessage{}, err
	}

	numberValue, err := strconv.ParseUint(row[4], 10, 32)
	if err != nil {
		return protocol.BetMessage{}, err
	}

	bet := protocol.BetMessage{
		Agency:    client.agency,
		Name:      row[0],
		Lastname:  row[1],
		Document:  uint32(documento),
		Birthdate: row[3],
		Number:    uint32(numberValue),
	}
	return bet, nil
}
