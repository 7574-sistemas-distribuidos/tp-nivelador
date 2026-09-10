package client

import (
	"net"
	"time"
	"bufio"
	"os"
	"fmt"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/protocol"
)

const CONNECTION_ATTEMPTS_MAX = 3
const CONNECTION_ATTEMPS_DELAY_MS = 1000 // 200
 
const RETRY_MAX = 5
const INIT_SEQ_NUM = 0

type ClientConfig struct {
	ServerHost string
	ServerPort string
	AgencyId   string
	BatchSize string
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

func (client *Client) Close() error {
	if client.conn != nil {
		return client.conn.Close()
	}
	return nil
}

func (client *Client) Run() error {
	const mainAction = "client-run"
	defer client.conn.Close()

	inputFile, err := os.Open(os.Getenv("INPUT_FILE"))
	if err != nil {
		logger.Error(mainAction, logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}
	defer inputFile.Close()

	outputFile, err := os.Create(os.Getenv("OUTPUT_FILE"))
	if err != nil {
		logger.Error(mainAction, logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}
	defer outputFile.Close()
	
	seq_num := INIT_SEQ_NUM
	batchSize, err := protocol.StringToInt(client.config.BatchSize)
	if err != nil {
		logger.Error(mainAction, logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}
	if err := sendInitPacket(client.conn, &seq_num, client.config.AgencyId); err != nil {
		logger.Error("send-init", logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}

	if err := sendBets(client.conn, &seq_num, inputFile, client.config.AgencyId, batchSize) ; err != nil {
		logger.Error("send-bets" , logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}

	if err := sendEOF(client.conn, &seq_num, client.config.AgencyId) ; err != nil {
		logger.Error("send-EOF" , logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}
	
	if err := receiveWinners(client.conn, seq_num, outputFile); err != nil {
		logger.Error("receive-winner", logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}

	return nil
}

func sendInitPacket(conn net.Conn, seq_num *int, agencyId string) error {
	const mainAction = "send-init"
	logger.Info(mainAction, logger.Success, "Sending AGENCY-ID: ", agencyId)
	sent_succesfully := false
	for retries := 0; retries < RETRY_MAX && !sent_succesfully; retries++ {
		if err := protocol.SendInit(conn, *seq_num, []byte(agencyId)); err != nil {
			logger.Error(mainAction, logger.Fail, "agency-id", agencyId)
			return err
		}
		ack, err := protocol.ReceiveFrom(conn)
		if err != nil {
			logger.Error(mainAction, logger.Fail, "agency-id", agencyId)
			return err
		}
		sent_succesfully = *seq_num == ack.SequenceNumber()
	}
	if !sent_succesfully {
		return fmt.Errorf("no se pudo enviar INIT después de %d reintentos", RETRY_MAX)
	}
	*seq_num = *seq_num + 1
	return  nil
}

func sendBets(conn net.Conn, seq_num *int, inputFile *os.File, agencyId string, batchSize int) error {
	const mainAction = "send-bets"
	lineCount := 0
	scanner := bufio.NewScanner(inputFile)
	var batch []*protocol.Bet
	for scanner.Scan() {
		line := scanner.Text()
		lineCount++
 
		bet, err := protocol.ParseBetFromCSVLine(line, agencyId)
		if err != nil {
			logger.Error(mainAction, "parse-error", "line", lineCount, "error", err)
			continue
		}

		batch = append(batch, bet)

        if len(batch) == batchSize {
            if err := sendBatch(conn, seq_num, batch); err != nil {
                return err
            }
            batch = nil
        }
	}

    if len(batch) > 0 {
        if err := sendBatch(conn, seq_num, batch); err != nil {
            return err
        }
    }

    if err := scanner.Err(); err != nil {
        logger.Error("scan-input-file", logger.Fail, "agency-id", agencyId)
        return err
    }

    logger.Info("send-bets", logger.Success, "agency-id", agencyId, "lines-read", lineCount)
    return nil
}

func sendBatch(conn net.Conn, seq_num *int, bets []*protocol.Bet) error {
    payload, err := protocol.SerializeBatch(bets)
    if err != nil {
        return err
    }
    if err := protocol.SendRequest(conn, *seq_num, payload); err != nil {
        return err
    }
    ack, err := protocol.ReceiveFrom(conn)
    if err != nil {
        return err
    }
    if ack.SequenceNumber() != *seq_num {
        return fmt.Errorf("ACK incorrecto")
    }
    if string(ack.Payload()) == "ERROR" {
        return fmt.Errorf("servidor rechazó el lote")
    }
    *seq_num++
    return nil
}

func sendEOF(conn net.Conn, seq_num *int, agencyId string) error {
	const mainAction = "send-EOF"
	logger.Info(mainAction, logger.Success,"Sending EOF")
	sent_succesfully := false
	for retries := 0; retries < RETRY_MAX && !sent_succesfully; retries++ {
		if err := protocol.SendEOF(conn, *seq_num); err != nil {
			logger.Error("send-eof", logger.Fail, "agency-id", agencyId)
			return err
		}
		ack, err := protocol.ReceiveFrom(conn)
		if err != nil {
			logger.Error("receive-ack", logger.Fail, "agency-id", agencyId)
			return err
		}
		sent_succesfully = *seq_num == ack.SequenceNumber()
	}
	if !sent_succesfully {
		return fmt.Errorf("no se pudo enviar EOF después de %d reintentos", RETRY_MAX)
	}
	*seq_num = *seq_num + 1
	return nil
}

func receiveWinners(conn net.Conn, seq_num int, outputFile *os.File) error {
	const mainAction = "receive-winner"
	for {
		pkt, err := protocol.ReceiveFrom(conn)
		if err != nil {
			logger.Error("receive-winner", logger.Fail, "error", err)
			return err
		}

		if pkt.Type() == protocol.EOF {
			if err := protocol.SendACK(conn, pkt.SequenceNumber(), []byte{}); err != nil {
				logger.Error("send-ack-eof", logger.Fail, "error", err)
				return err
			}
			logger.Info(mainAction, logger.Success, "EOF-final-received")
			break
		} else if pkt.Type() == protocol.RESPONSE {
			var bet protocol.Bet
        	if err := bet.FromBytes(pkt.Payload()); err != nil{
				logger.Error("parse-winner", logger.Fail, "error", err)
				protocol.SendACK(conn, seq_num, []byte{})
				continue
			}

			// Escribir en archivo de salida
			line, _ := protocol.ParseCSVLineFromBet(bet)
			if _, err := outputFile.WriteString(line + "\n"); err != nil {
				logger.Error("write-output", logger.Fail, "error", err)
				return err
			}

			// Enviar ACK confirmando recepción
			if err := protocol.SendACK(conn, pkt.SequenceNumber(), []byte{}); err != nil {
				logger.Error("send-ack-response", logger.Fail, "error", err)
				return err
			}
			logger.Info(mainAction, logger.InProgress, "winner-received", "seq", pkt.SequenceNumber())
		} else {
			logger.Error("unexpected-packet", "type", pkt.Type())
			return fmt.Errorf("paquete inesperado: %v", pkt.Type())
		}
	}
	return nil
}

