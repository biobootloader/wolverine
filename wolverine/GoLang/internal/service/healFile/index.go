package healFile

import (
	"errors"
)

func HealFile(sourceFilename, resultFilename, apiToken, model, prompt string, attemptsToTry int) error {
	var compileError string

	if isCompilable(sourceFilename, &compileError) {
		return nil
	}

	// initial attempt
	err := attempt(sourceFilename, resultFilename, compileError, apiToken, model, prompt)
	if err != nil {

		return err
	}

	if isCompilable(resultFilename, &compileError) {
		return nil
	}

	// if didn't work, try to heal file, which you are working with
	sourceFilename = resultFilename

	attempts := 1

	for {
		if attempts >= attemptsToTry {
			return errors.New(string(attemptsToTry) + " attempts to heal file failed")
		}

		attempts++

		err = attempt(sourceFilename, resultFilename, compileError, apiToken, model, prompt)
		if err != nil {
			return err
		}

		if isCompilable(resultFilename, &compileError) {
			break
		}
	}

	return nil
}
