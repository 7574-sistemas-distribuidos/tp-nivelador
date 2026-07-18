package logger

import (
	"fmt"
	"log/slog"
)

type LogResult string

const (
	InProgress LogResult = "in-progress"
	Fail       LogResult = "fail"
	Success    LogResult = "success"
)

func buildMessage(action string, result LogResult) string {
	return fmt.Sprintf("action=%s result=%s", action, result)
}

func Info(action string, result LogResult, args ...any) {
	message := buildMessage(action, result)
	slog.Info(message, args...)
}

func Warn(action string, result LogResult, args ...any) {
	message := buildMessage(action, result)
	slog.Warn(message, args...)
}

func Error(action string, result LogResult, args ...any) {
	message := buildMessage(action, result)
	slog.Error(message, args...)
}
