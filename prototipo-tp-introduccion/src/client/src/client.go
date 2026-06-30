package client

import (
	"fmt"
	"log/slog"
	"net"
	"time"
)

const CONNECTION_ATTEMPTS_MAX = 3
const CONNECTION_ATTEMPS_DELAY_MS = 200

const ECHO_CLIENT_BUFFER_SIZE = 512
const ECHO_CLIENT_MESSAGE_AMOUNT = 3
const ECHO_CLIENT_MESSAGE_DELAY_MS = 1000

type ClientConfig struct {
	ServerHost string
	ServerPort string
	InputFile  string
	OutputFile string
	AgencyId   string
}

type Client struct {
	conn   net.Conn
	config ClientConfig
}

func NewClient(config ClientConfig) (*Client, error) {
	conn, err := connectToServer(config.ServerHost, config.ServerPort)
	if err != nil {
		return nil, err
	}

	client := &Client{conn: conn, config: config}
	return client, nil
}

func connectToServer(host, port string) (net.Conn, error) {
	var err error
	var conn net.Conn

	for range CONNECTION_ATTEMPTS_MAX {
		conn, err = net.Dial("tcp", host+":"+port)
		if err != nil {
			slog.Warn("Retrying connection...")
			time.Sleep(CONNECTION_ATTEMPS_DELAY_MS * time.Millisecond)
			continue
		}
		slog.Info("Connected to server")
		break
	}

	return conn, err
}

func (client *Client) Run() error {
	defer client.conn.Close()

	for messageId := range ECHO_CLIENT_MESSAGE_AMOUNT {
		clientMessage := fmt.Sprintf("agency_id=%s message_id=%d", client.config.AgencyId, messageId)
		slog.Info("Sending message " + clientMessage)

		_, err := client.conn.Write([]byte(clientMessage))
		if err != nil {
			slog.Warn("Error while sending message to server")
			return err
		}

		responseBuffer := make([]byte, ECHO_CLIENT_BUFFER_SIZE)
		_, err = client.conn.Read(responseBuffer)
		if err != nil {
			slog.Warn("Error while receiving message from server")
			return err
		}
		responseMessage := fmt.Sprintf("Received message %s", responseBuffer)
		slog.Info(responseMessage)

		time.Sleep(ECHO_CLIENT_MESSAGE_DELAY_MS * time.Millisecond)
	}

	return nil
}
