package service

import (
	"errors"
	"os"
)

func PrepareNewFile(backupFilename string) error {
	err := createNewFile(backupFilename)
	if err != nil {
		return errors.New("failed to prepare file with fixes")
	}

	return nil
}

func createNewFile(backupFilename string) error {
	// Create the file
	file, err := os.Create(backupFilename)
	if err != nil {
		return err
	}
	defer file.Close()

	return nil
}
