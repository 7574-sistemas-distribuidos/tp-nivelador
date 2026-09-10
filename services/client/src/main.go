package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/signal"
	"strconv"
	"syscall"

	client "github.com/7574-sistemas-distribuidos/tp-nivelador/src/client"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
)

const DEFAULT_BATCH_SIZE = 100

func loadConfig() (client.ClientConfig, error) {
	rawAgencyId := os.Getenv("AGENCY_ID")
	if rawAgencyId == "" {
		return client.ClientConfig{}, errors.New("AGENCY_ID environment variable is required")
	}

	agencyId, err := strconv.Atoi(rawAgencyId)
	if err != nil {
		return client.ClientConfig{}, fmt.Errorf("AGENCY_ID must be a number: %w", err)
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

	batchSize := DEFAULT_BATCH_SIZE
	if rawBatchSize := os.Getenv("BATCH_SIZE"); rawBatchSize != "" {
		batchSize, err = strconv.Atoi(rawBatchSize)
		if err != nil {
			return client.ClientConfig{}, fmt.Errorf("BATCH_SIZE must be a number: %w", err)
		}
		if batchSize <= 0 {
			return client.ClientConfig{}, fmt.Errorf("BATCH_SIZE must be positive, got %d", batchSize)
		}
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

func run() int {
	ctx, stopListeningForSignals := signal.NotifyContext(context.Background(), syscall.SIGTERM)
	defer stopListeningForSignals()

	config, err := loadConfig()
	if err != nil {
		logger.Error("load-config", logger.Fail, "err", err)
		return 1
	}

	client, err := client.NewClient(config)
	if err != nil {
		logger.Error("client-new", logger.Fail, "err", err)
		return 1
	}

	if err := client.Run(ctx); err != nil {
		if ctx.Err() != nil {
			logger.Info("client-shutdown", logger.Success, "agency-id", config.AgencyId)
			return 0
		}
		logger.Error("client-run", logger.Fail, "err", err)
		return 1
	}
	return 0
}

func main() {
	os.Exit(run())
}
