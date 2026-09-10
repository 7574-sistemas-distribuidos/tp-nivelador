package main

import (
	"errors"
	"os"
	"os/signal"
	"syscall"

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

	batchSize := os.Getenv("BATCH_SIZE")
	if batchSize == "" {
		return client.ClientConfig{}, errors.New("BATCH_SIZE environment variable is required")
	}

	return client.ClientConfig{
		ServerHost: serverHost,
		ServerPort: serverPort,
		AgencyId:   agencyId,
		BatchSize:  batchSize,
	}, nil
}

func run() int {
	config, err := loadConfig()
	if err != nil {
		logger.Error("load-config", logger.Fail, "err", err)
		return 1
	}

	c, err := client.NewClient(config)
	if err != nil {
		logger.Error("client-new", logger.Fail, "err", err)
		return 1
	}

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGTERM)

	done := make(chan error, 1)
	go func() {
		done <- c.Run()
	}()

	select {
	case err := <-done:
		if err != nil {
			logger.Error("client-run", logger.Fail, "err", err)
			return 1
		}
		return 0
	case sig := <-sigCh:
		logger.Info("sigterm-received", logger.InProgress, "signal", sig.String())
		c.Close()
		<-done
		logger.Info("shutdown", logger.Success)
		return 0
	}
}

func main() {
	os.Exit(run())
}
