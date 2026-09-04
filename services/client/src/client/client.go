package client

import (
	"bufio"
	"encoding/csv"
	"fmt"
	"net"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

const CONNECTION_ATTEMPTS_MAX = 30
const CONNECTION_ATTEMPS_DELAY_MS = 200

const ECHO_END_CONNECTION = "END"
const ECHO_ACK_OK = "OK"

var INPUT_FILE = os.Getenv("INPUT_FILE")
var OUTPUT_FILE = os.Getenv("OUTPUT_FILE")
var BATCH_SIZE, _ = strconv.Atoi(os.Getenv("BATCH_SIZE"))

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
	const mainAction = "send-input-file"
	defer client.conn.Close()
	f, err := os.Open(INPUT_FILE)
	if err != nil {
		logger.Error("file-read", logger.Fail, "file", INPUT_FILE, "error", err)
		return err
	}
	defer f.Close()

	out, err := os.Create(OUTPUT_FILE)
	if err != nil {
		logger.Error("file-write", logger.Fail, "file", OUTPUT_FILE, "error", err)
		return err
	}
	defer out.Close()

	csvReader := csv.NewReader(f)
	messageId := 0
	eof := false
	for eof == false {
		var batch [][]string
		for i := 0; i < BATCH_SIZE; i += 1 {

			row, _ := csvReader.Read()
			if row == nil {
				eof = true
				break
			}
			batch = append(batch, row)
		}

		messageArgs := []any{"agency-id", client.config.AgencyId, "message-id", messageId}
		logger.Info(mainAction, logger.InProgress, messageArgs...)
		var clientMessage string
		for _, row := range batch {
			rowMessage := strings.Join(append([]string{client.config.AgencyId}, row...), ",")
			clientMessage += rowMessage
			clientMessage += "\n"
		}
		payload := []byte(clientMessage)
		header := []byte(fmt.Sprintf("%08d", len(payload)))
		if err := safe_socket.SendAll(client.conn, append(header, payload...)); err != nil {
			logger.Error("send-message", logger.Fail, messageArgs...)
			return err
		}

		_, err := safe_socket.RecvAll(client.conn, len(ECHO_ACK_OK))
		if err != nil {
			logger.Error("recv-response", logger.Fail, messageArgs...)
			return err
		}
		messageId += 1

	}

	endHeader := []byte(fmt.Sprintf("%08d", len(ECHO_END_CONNECTION)))
	if err := safe_socket.SendAll(client.conn, append(endHeader, []byte(ECHO_END_CONNECTION)...)); err != nil {
		logger.Error("send-message", logger.Fail)
		return err
	}

	reader := bufio.NewReader(client.conn)
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			logger.Error("recv-response", logger.Fail, "agency-id", client.config.AgencyId)
			return err
		}
		line = strings.TrimRight(line, "\n")
		if line == ECHO_END_CONNECTION {
			break
		}
		if _, err := out.WriteString(line + "\n"); err != nil {
			logger.Error("write-response", logger.Fail, "agency-id", client.config.AgencyId)
			return err
		}
	}

	logger.Info(mainAction, logger.Success, "agency-id", client.config.AgencyId)

	return nil
}
