package healFile

import (
	"encoding/json"
)

func validateResponse(response string) (GPTResponse, error) {
	/*
		The original idea of recursive forcing response
		to be in JSON format was abandoned, because there is
		no need to make it so complicated. Anyway we make
		requests until we get valid JSON response.
	*/

	var jsonGPTResponse GPTResponse
	err := json.Unmarshal([]byte(response), &jsonGPTResponse)
	if err != nil {
		return GPTResponse{}, err
	}

	return jsonGPTResponse, nil
}
