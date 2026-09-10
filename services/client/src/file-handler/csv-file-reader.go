package filehandler

import (
	"encoding/csv"
	"errors"
	"io"
	"os"
)

type BatchReader struct {
	file   *os.File
	reader *csv.Reader
}

func NewCSVReader(filePath string) (*BatchReader, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	return &BatchReader{
		file:   file,
		reader: csv.NewReader(file),
	}, nil
}

func (br *BatchReader) ReadBatch(batchSize int) ([][]string, bool, error) {
	records := make([][]string, 0, batchSize)

	for len(records) < batchSize {
		record, err := br.reader.Read()
		if errors.Is(err, io.EOF) {
			return records, false, nil
		}
		if err != nil {
			return records, false, err
		}
		records = append(records, record)
	}

	return records, true, nil
}

func (br *BatchReader) Close() error {
	return br.file.Close()
}
