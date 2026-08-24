package main

import (
	"errors"
	"os"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/client"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
)

func loadConfig() (client.Config, error) {
	agencyId := os.Getenv("AGENCY_ID")

	if agencyId == "" {
		return client.Config{}, errors.New("AGENCY_ID environment variable is required")
	}
	serverHost := os.Getenv("SERVER_HOST")

	if serverHost == "" {
		return client.Config{}, errors.New("SERVER_HOST environment variable is required")
	}
	serverPort := os.Getenv("SERVER_PORT")

	if serverPort == "" {
		return client.Config{}, errors.New("SERVER_PORT environment variable is required")
	}
	inputFile := os.Getenv("INPUT_FILE")

	if inputFile == "" {
		return client.Config{}, errors.New("INPUT_FILE environment variable is required")
	}
	outputFile := os.Getenv("OUTPUT_FILE")

	if outputFile == "" {
		return client.Config{}, errors.New("OUTPUT_FILE environment variable is required")
	}
	return client.Config{
		ServerHost: serverHost,
		ServerPort: serverPort,
		AgencyId:   agencyId,
		InputFile:  inputFile,
		OutputFile: outputFile,
	}, nil
}

func run() int {
	config, err := loadConfig()

	if err != nil {
		logger.Error("load-config", logger.Fail, "err", err)
		return 1
	}
	newClient, err := client.NewClient(config)

	if err != nil {
		logger.Error("client-new", logger.Fail, "err", err)
		return 1
	}
	if err := newClient.Run(); err != nil {
		logger.Error("client-run", logger.Fail, "err", err)
		return 1
	}
	return 0
}

func main() {
	os.Exit(run())
}
