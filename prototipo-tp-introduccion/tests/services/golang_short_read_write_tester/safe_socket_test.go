package safe_socket

import (
	"fmt"
	"io"
	"math/rand"
	"strings"
	"testing"

	"github.com/stretchr/testify/require"
)

type testCase struct {
	data         []byte
	maxChunkSize int
}

var cases = []testCase{
	{[]byte("hello-world"), 4},
	{[]byte("Robert Smith,50000000,7574"), 8},
	{[]byte("ack"), 1},
	{[]byte(strings.Repeat("a", 2048)), 32},
}

// Helper function to run test suite
func TestShortReadWrite(
	t *testing.T,
) {
	testShortRead(t, RecvAll)
	testShortWrite(t, SendAll)
}

func testShortRead(t *testing.T,
	read_all func(
		r io.Reader,
		n int,
	) ([]byte, error),
) {
	t.Run("Short Read", func(t *testing.T) {
		for _, tc := range cases {
			r := NewShortReader(tc.data, tc.maxChunkSize)
			data, err := read_all(r, len(tc.data))
			require.NoError(t, err, "read_all returned an error")
			require.Equal(t, len(tc.data), len(data), "returned data should be the same length")
			require.Equal(t, tc.data, data, "Returned data should be equal match")
		}
	})
}

func testShortWrite(t *testing.T,
	write_all func(
		w io.Writer,
		b []byte,
	) error,
) {
	t.Run("Short Write", func(t *testing.T) {
		for _, tc := range cases {
			w := NewShortWriter(tc.maxChunkSize)
			err := write_all(w, tc.data)
			require.NoError(t, err, "write_all returned an error")
			require.Equal(t, len(tc.data), len(w.data), "returned data should be the same length")
			require.Equal(t, tc.data, w.data, "Returned data should be equal match")
		}
	})
}

// ShortReader mocks io.Reader maliciously causing short read
type ShortReader struct {
	data         []byte
	maxChunkSize int
}

func NewShortReader(data []byte, maxChunkSize int) io.Reader {
	return &ShortReader{data, maxChunkSize}
}

var _ io.Reader = (*ShortReader)(nil)

// Read implements [io.Reader].
func (s *ShortReader) Read(p []byte) (n int, err error) {
	if len(s.data) == 0 {
		return 0, io.EOF
	}

	destBufSize := len(p)
	maxAmountToReturn := min(destBufSize, s.maxChunkSize)
	maxDataLenToReturn := rand.Intn(maxAmountToReturn + 1)
	lenToReturn := min(maxDataLenToReturn, len(s.data))
	dataToReturn := s.data[:lenToReturn]
	s.data = s.data[lenToReturn:]
	n = copy(p, dataToReturn)
	if n != lenToReturn {
		return 0, fmt.Errorf("Internal Error: Short Read: fail to copy to dest: copy returned %d but size was %d", n, destBufSize)
	}
	return n, nil
}

// ShortWriter mocks io.Writer maliciously causing short writes
type ShortWriter struct {
	data         []byte
	maxChunkSize int
}

func NewShortWriter(maxChunkSize int) *ShortWriter {
	return &ShortWriter{
		data:         []byte{},
		maxChunkSize: maxChunkSize,
	}
}

var _ io.Writer = (*ShortWriter)(nil)

// Write implements [io.Writer].
func (w *ShortWriter) Write(p []byte) (n int, err error) {
	srcSize := len(p)
	maxSize := min(srcSize, w.maxChunkSize)
	n = rand.Intn(maxSize + 1)
	dataToWrite := p[:n]
	w.data = append(w.data, dataToWrite...)
	return n, nil
}
