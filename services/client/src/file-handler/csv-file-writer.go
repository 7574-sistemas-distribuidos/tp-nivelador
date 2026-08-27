package filehandler

import (
	"encoding/csv"
	"os"
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

	return nil
}
