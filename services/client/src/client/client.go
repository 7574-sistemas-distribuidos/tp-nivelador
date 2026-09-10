package client

import (
	"bytes"
	"context"
	"fmt"
	"net"
	"strconv"
	"strings"
	"time"

	"bufio"
	"os"
	"path/filepath"

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

// el limite de agencyId esta relacionado con el protocolo
func NewClient(ctx context.Context, config ClientConfig) (*Client, error) {

	agencyId, err := strconv.Atoi(config.AgencyId)
	if err != nil {
		return nil, err
	}

	if agencyId < 0 || agencyId > 0xFF {
		return nil, fmt.Errorf("agency id invalido: %d, debe estar entre 0 y 255", agencyId)
	}

	batchSize, err := strconv.Atoi(config.BatchSize)
	if err != nil {
		return nil, err
	}

	if batchSize < 1 {
		return nil, fmt.Errorf("tamaño de batch invalido: %d", batchSize)
	}

	conn, err := connectToServer(ctx, config.ServerHost, config.ServerPort)
	if err != nil {
		logger.Warn("connect-to-server", logger.Fail)
		return nil, err
	}

	return &Client{conn: conn, config: config, agency: byte(agencyId), batchSize: batchSize, ctx: ctx}, nil
}

// el select contra el ctx logra que no se tenga que esperar el delay completo
// si llega SIGTERM mientras se espera
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

// para lograr el cierre durante la comunicacion, que puede pasar
// durante un read o write, se cierra la conexion en el defer de
// Run y en la goroutine que espera a que se cancele el contexto
//
// el orden sendBets -> sendEnd -> receiveWinners le avisa
// al server cuando se enviaron todas las apuestas
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

// encodedeNewBet se reutiliza entre iteraciones
// en las iteraciones se acumula por batch y se hace el envio cuando se llena
// hay un envio final fuera del loop para el remanente
func (client *Client) sendBets() error {
	inputFile, err := os.Open(client.config.InputFile)
	if err != nil {
		logger.Error("open-input-file", logger.Fail)
		return err
	}

	defer inputFile.Close()

	scanner := bufio.NewScanner(inputFile)
	batchBets := 0
	batchBytes := 0
	var batch []byte
	var encodedNewBet []byte

	for scanner.Scan() {
		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}

		encodedNewBet, err = client.encodeBet(encodedNewBet[:0], line)
		if err != nil {
			return err
		}

		batch, batchBytes, batchBets, err = client.accumulateOrSendBatch(batch, batchBets, batchBytes, encodedNewBet)
		if err != nil {
			return err
		}
	}

	if err := scanner.Err(); err != nil {
		logger.Error("read-input", logger.Fail)
		return err
	}

	if len(batch) > 0 {
		if err := client.SendBatch(batch); err != nil {
			return err
		}
	}
	return nil
}

// se corta y se envia el batch por dos razones distintas:
// llegar a batch_size o estar por superar el largo de payload maximo
func (client *Client) accumulateOrSendBatch(batch []byte, batchBets int, batchBytes int, encodedNewBet []byte) ([]byte, int, int, error) {
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

// sendBuf se reutiliza entre llamadsa a SendBatch (en
// vez de alocar un buffer por batch)
// la idea es que guarda la capacidad maxima de batch
// y no vuelve a crecer despues de eso
// se envia un batch y se espera el ack del server
func (client *Client) SendBatch(payload []byte) error {
	sendBuf, err := protocol.AppendBatch(client.sendBuf[:0], client.agency, payload)
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

// para no depender de la existencia de la carpeta, se crea si no existe
// recibimos winner -> mandamos ack
// despues de cada winner, se hace flush, si se corta
// la ejecucion lo recibido ya habra quedado persistido
// tiene un costo asociado, quizas no conviene
func (client *Client) receiveWinners() error {
	if err := os.MkdirAll(filepath.Dir(client.config.OutputFile), 0o755); err != nil {
		logger.Error("create-output-dir", logger.Fail)
		return err
	}

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

		line := strings.Join(row, ",") + "\n"
		if _, err := writer.WriteString(line); err != nil {
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

// se usa bytes.Cut para no alocar con bytes.Split
// el ultimo chequeo es para asegurarnos que no hay mas campos
func (client *Client) encodeBet(buf []byte, line []byte) ([]byte, error) {
	name, rest, ok := bytes.Cut(line, []byte(","))
	if !ok {
		return nil, fmt.Errorf("línea invalida, se esperaban 5 campos: %q", line)
	}

	lastname, rest, ok := bytes.Cut(rest, []byte(","))
	if !ok {
		return nil, fmt.Errorf("línea invalida, se esperaban 5 campos: %q", line)
	}

	documentoBytes, rest, ok := bytes.Cut(rest, []byte(","))
	if !ok {
		return nil, fmt.Errorf("línea invalida, se esperaban 5 campos: %q", line)
	}

	birthdate, numberBytes, ok := bytes.Cut(rest, []byte(","))
	if !ok {
		return nil, fmt.Errorf("línea invalida, se esperaban 5 campos: %q", line)
	}

	if bytes.Contains(numberBytes, []byte(",")) {
		return nil, fmt.Errorf("línea invalida, se encontraron mas de 5 campos: %q", line)
	}

	documento, err := strconv.ParseUint(string(documentoBytes), 10, 32)
	if err != nil {
		return nil, err
	}

	numberValue, err := strconv.ParseUint(string(numberBytes), 10, 32)
	if err != nil {
		return nil, err
	}

	return protocol.AppendBet(buf, name, lastname, birthdate, uint32(documento), uint32(numberValue))
}
