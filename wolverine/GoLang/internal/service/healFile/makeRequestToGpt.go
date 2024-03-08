package healFile

import (
	"bytes"
	"encoding/json"
	"net/http"
)

func makeRequestToGPT(code, compileError, apiToken, model string, prompt string) (GPTResponse, error) {

	if compileError == "" {
		prompt += "\n\nHere is the script that needs fixing:\n\n" +
			code + "\n\n" +
			"Please provide your suggested changes, and remember to stick to the " +
			"exact format as described above."
	} else {
		prompt += "\n\nHere is the script that needs fixing:\n\n" +
			code + "\n\n" +
			"Here is the error message:\n\n" +
			compileError + "\n" +
			"Please provide your suggested changes, and remember to stick to the " +
			"exact format as described above."
	}

	var request = Request{
		Model:     model,
		Prompt:    prompt,
		MaxTokens: 1000,
	}

	reqBody, err := json.Marshal(request)
	if err != nil {
		return GPTResponse{}, err
	}

	url := "https://api.openai.com/v1/completions"

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(reqBody))
	if err != nil {
		return GPTResponse{}, err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiToken)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return GPTResponse{}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return GPTResponse{}, err
	}

	var response Response
	err = json.NewDecoder(resp.Body).Decode(&response)
	if err != nil {
		return GPTResponse{}, err
	}

	gptResponse, err := validateResponse(response.Choices[0].Text)
	if err != nil {
		return GPTResponse{}, err
	}

	return gptResponse, nil
}
