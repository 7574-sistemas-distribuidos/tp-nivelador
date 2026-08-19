FROM golang:1.24-alpine3.23 AS builder
COPY ./tests/services/golang_short_read_write_tester .
COPY ./services/client/src/safe_socket/safe_socket.go safe_socket.go
ENTRYPOINT ["go", "test"]
