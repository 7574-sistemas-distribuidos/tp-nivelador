package main

import (
	"errors"
	"os"

	client "github.com/7574-sistemas-distribuidos/tp-nivelador/src/client"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
)

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
	inputFilePath := os.Getenv("INPUT_FILE")
	if inputFilePath == "" {
		return client.ClientConfig{}, errors.New("INPUT_FILE environment variable is required")
	}
	outputDir := os.Getenv("OUTPUT_FILE")
	if outputDir == "" {
		return client.ClientConfig{}, errors.New("OUTPUT_FILE environment variable is required")
	}

	bacthSize := os.Getenv("BATCH_SIZE")
	if bacthSize == "" {
		return client.ClientConfig{}, errors.New("BATCH_SIZE environment variable is required")
	}

	return client.ClientConfig{
		ServerHost:    serverHost,
		ServerPort:    serverPort,
		AgencyId:      agencyId,
		InputFilePath: inputFilePath,
		OutputDir:     outputDir,
		BatchSize:     bacthSize,
	}, nil
}

func run() int {
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

	if err := client.Run(); err != nil {
		logger.Error("client-run", logger.Fail, "err", err)
		return 1
	}
	return 0
}

func main() {
	os.Exit(run())
}
