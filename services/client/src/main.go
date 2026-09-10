package main

import (
	"context"
	"errors"
	"os"
	"os/signal"
	"syscall"

	client "github.com/7574-sistemas-distribuidos/tp-nivelador/src/client"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
)

// Carga la configuracion del cliente desde variables
// de entorno y devuelve un objeto ClientConfig
func loadConfig() (client.ClientConfig, error) {
	agencyId := os.Getenv("AGENCY_ID")
	if agencyId == "" {
		return client.ClientConfig{}, errors.New("AGENCY_ID environment variable is required")
	}

	serverHost := os.Getenv("SERVER_HOST")
	if serverHost == "" {
		return client.ClientConfig{}, errors.New("SERVER_HOST environment variable is required")
	}

	serverPort := os.Getenv("SERVER_PORT")
	if serverPort == "" {
		return client.ClientConfig{}, errors.New("SERVER_PORT environment variable is required")
	}

	inputFile := os.Getenv("INPUT_FILE")
	if inputFile == "" {
		return client.ClientConfig{}, errors.New("INPUT_FILE environment variable is required")
	}

	outputFile := os.Getenv("OUTPUT_FILE")
	if outputFile == "" {
		return client.ClientConfig{}, errors.New("OUTPUT_FILE environment variable is required")
	}

	batchSize := os.Getenv("BATCH_SIZE")
	if batchSize == "" {
		return client.ClientConfig{}, errors.New("BATCH_SIZE environment variable is required")
	}

	return client.ClientConfig{
		ServerHost: serverHost,
		ServerPort: serverPort,
		AgencyId:   agencyId,
		InputFile:  inputFile,
		OutputFile: outputFile,
		BatchSize:  batchSize,
	}, nil
}

// ctx se cancela al recibir SIGTERM y se propaga a las llamadas para
// cortar al instante la ejecucion del cliente
// defer cancel evita que la goroutine que escucha el canal en Run
// quede bloqueada para siempre si el cliente termina normalmente
func run() int {
	config, err := loadConfig()
	if err != nil {
		logger.Error("load-config", logger.Fail, "err", err)
		return 1
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	sigChannel := make(chan os.Signal, 1)
	signal.Notify(sigChannel, syscall.SIGTERM)

	go func() {
		<-sigChannel
		logger.Info("sigterm", logger.InProgress)
		cancel()
	}()

	client, err := client.NewClient(ctx, config)
	if err != nil {
		return checkError(ctx, err, "client-new", "sigterm")
	}

	if err := client.Run(); err != nil {
		return checkError(ctx, err, "client-run", "sigterm")
	}
	return 0
}

func main() {
	os.Exit(run())
}

func checkError(ctx context.Context, err error, action string, reason string) int {
	if ctx.Err() != nil {
		logger.Info(action, logger.Success, "reason", reason)
		return 0
	}
	logger.Error(action, logger.Fail, "err", err)
	return 1
}
