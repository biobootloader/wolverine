package service

import (
	"errors"
	"os"
	"regexp"
)

func ReceiveFile() (string, error) {
	args := os.Args[1:]
	if len(args) != 1 {
		return "", errors.New("entered invalid flags")
	} else {
		filename := args[0]
		if !isValidFilename(filename) {
			return "", errors.New("entered invalid filename")
		}

		return filename, nil
	}
}

func isValidFilename(filename string) bool {
	validFilenameRegex := regexp.MustCompile(`^[a-zA-Z0-9_.-]*$`)
	return validFilenameRegex.MatchString(filename)
}
