package healFile

import (
	"fmt"
	"strings"
	"wolverine/pkg/cli"
)

func applyChanges(sourceFilename, targetFilename string, changes GPTResponse) error {
	fileLines, err := readFileLines(sourceFilename)
	if err != nil {
		return err
	}

	sortChanges(&changes)

	// define entities only after sorting the object
	explanations := changes.Explanations
	actions := changes.Actions

	for _, action := range actions {
		switch action.Operations[0].Operation {
		case DeleteOperationType:
			fmt.Println("Delete Operation:")
			printExplanations(explanations, action, cli.PrintRed)

			for _, operation := range action.Operations {
				deleteLine(&fileLines, operation.Line)
			}

		case InsertOperationType:
			fmt.Println("Insert Operation:")
			printExplanations(explanations, action, cli.PrintGreen)

			for _, operation := range action.Operations {
				insertLine(&fileLines, operation.Line, operation.Content)
			}
		case ReplaceOperationType:
			fmt.Println("Replace Operation:")
			printExplanations(explanations, action, cli.PrintYellow)

			for _, operation := range action.Operations {
				replaceLine(&fileLines, operation.Line, operation.Content)
			}
		}
	}

	entireCode := strings.Join(fileLines, "\n")
	err = writeToExistingFile(targetFilename, entireCode)
	if err != nil {
		return err
	}

	return nil
}

func sortChanges(changes *GPTResponse) {
	// reverse the actions
	for i := 0; i < len(changes.Actions)/2; i++ {
		changes.Actions[i], changes.Actions[len(changes.Actions)-i-1] = changes.Actions[len(changes.Actions)-i-1], changes.Actions[i]
	}

	// reverse the explanations
	for i := 0; i < len(changes.Explanations)/2; i++ {
		changes.Explanations[i], changes.Explanations[len(changes.Explanations)-i-1] = changes.Explanations[len(changes.Explanations)-i-1], changes.Explanations[i]
	}
}

func deleteLine(fileLines *[]string, line int) {
	// GPT would respond like 1st line has an error, but we work with 0th item, not 1st
	line--
	*fileLines = append((*fileLines)[:line], (*fileLines)[line+1:]...)
}

func insertLine(fileLines *[]string, line int, content string) {
	// GPT would respond like 1st line has an error, but we work with 0th item, not 1st
	line--
	*fileLines = append((*fileLines)[:line+1], append([]string{content}, (*fileLines)[line+1:]...)...)
}

func replaceLine(fileLines *[]string, line int, content string) {
	// GPT would respond like 1st line has an error, but we work with 0th item, not 1st
	line--
	(*fileLines)[line] = content
}

func printExplanations(explanations []GPTExplanation, action GPTAction, printFunc func(string)) {
	currentExplanationIndex := -1

	for i, explanation := range explanations {
		if explanation.Id == action.Id {
			currentExplanationIndex = i
			break
		}
	}

	if currentExplanationIndex == -1 {
		fmt.Println("The explanation is not provided.")
	} else {
		for _, explanation := range explanations[currentExplanationIndex].Messages {
			fmt.Println(explanation)
		}
	}

	for _, operation := range action.Operations {
		printFunc(operation.Content)
	}
}
