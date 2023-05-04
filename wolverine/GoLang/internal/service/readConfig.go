package service

import (
	"encoding/json"
	"errors"
	"os"
)

type Config struct {
	OPENAI_API_KEY string
	GPT_MODEL      string
}

func ReadConfig(path string, container *Config) error {
	configFile, err := os.Open(path)
	if err != nil {
		return errors.New("Failed to open config.json\nMake sure you have set all necessary fields to it and try again.")
	}
	defer configFile.Close()

	err = json.NewDecoder(configFile).Decode(container)
	if err != nil {
		return errors.New("Failed to read and decode config.json\nMake sure you have set all necessary fields to it and try again.")
	}
	return nil
}
