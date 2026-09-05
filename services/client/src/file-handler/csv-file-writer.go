package filehandler

import (
	"encoding/csv"
	"os"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
)

func WriteCSVFile(filePath string, records [][]string) error {
	file, err := os.Create(filePath)
	if err != nil {
		return err
	}
	defer file.Close()

	w := csv.NewWriter(file)
	w.WriteAll(records)

	if err := w.Error(); err != nil {
		return err
	}
	logger.Info("write-csv-file", logger.Success, "Successfully wrote CSV file to", filePath)
	return nil
}
