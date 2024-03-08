package healFile

func attempt(sourceFilename, targetFilename, compileError, apiToken, model, prompt string) error {
	// get file content
	code, err := getFileContent(sourceFilename)
	if err != nil {
		return err
	}

	// make request to gpt
	gptResponse, err := makeRequestToGPT(code, compileError, apiToken, model, prompt)
	if err != nil {
		return err
	}

	// apply changes: write them to the targetFilename
	err = applyChanges(sourceFilename, targetFilename, gptResponse)
	if err != nil {
		return err
	}

	return nil
}
