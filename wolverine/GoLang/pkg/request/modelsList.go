package request

import (
	"encoding/json"
	"io"
	"net/http"
)

type ModelStruct struct {
	Id string `json:"id"`
}

type ModelsListStruct struct {
	Data []ModelStruct `json:"data"`
}

var targetUrl = "https://api.openai.com/v1/models"

func ModelsList(apiKey string) ([]ModelStruct, error) {
	client := &http.Client{}

	req, err := http.NewRequest("GET", targetUrl, nil)
	if err != nil {
		return []ModelStruct{}, err
	}

	req.Header.Add("Authorization", "Bearer "+apiKey)

	resp, err := client.Do(req)
	if err != nil {
		return []ModelStruct{}, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return []ModelStruct{}, err
	}

	var modelsList ModelsListStruct
	err = json.Unmarshal(body, &modelsList)
	if err != nil {
		return []ModelStruct{}, err
	}

	return modelsList.Data, nil
}
