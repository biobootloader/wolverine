package main

import (
	"embed"
	"fmt"
	"github.com/joho/godotenv"
	"log"
	"os"
	"strconv"
	"wolverine/internal/service"
	"wolverine/internal/service/healFile"
)

//go:embed prompt.txt
var promptContent embed.FS

func main() {
	content, err := promptContent.ReadFile("prompt.txt")
	if err != nil {
		fmt.Println("Failed to read prompt.txt file")
		log.Println(err)
		return
	}

	prompt := string(content)

	godotenv.Load()

	gptModel := os.Getenv("GPT_MODEL")
	apiKey := os.Getenv("OPENAI_API_KEY")
	attemptsToTryString := os.Getenv("ATTEMPTS_TO_TRY")
	if gptModel == "" || apiKey == "" {
		log.Println("You need to set GPT_MODEL and OPENAI_API_KEY environment variables to run the program.")
		return
	}

	attemptsToTry, err := strconv.Atoi(attemptsToTryString)
	if err != nil || attemptsToTryString == "" {
		log.Println("ATTEMPTS_TO_TRY environment variable is invalid or not set. It should be an integer.")
		log.Println(err)
		return
	}

	sourceFilename, err := service.ReceiveFile()
	if err != nil {
		fmt.Println("Failed to extract a filename from the inputted string")
		log.Println(err)
		return
	}

	healedFilename := sourceFilename + "__fixed.go"
	sourceFilename += ".go"

	_, err = os.Stat(sourceFilename)
	if os.IsNotExist(err) {
		log.Println("The file you entered doesn't exist. Enter another one and try again.")
		return
	}

	// prepare file to be filled code with changes
	err = service.PrepareNewFile(healedFilename)
	if err != nil {
		fmt.Println("Failed to prepare a new file to have the code with changes")
		log.Println(err)
		return
	}

	// check the inputted model
	modelIsValid := service.ValidateGPTModel(apiKey, gptModel)
	if !modelIsValid {
		log.Println("The GPT model you entered is invalid or doesn't exist. Enter another one and try again.")
		return
	}

	err = healFile.HealFile(sourceFilename, healedFilename, apiKey, gptModel, prompt, attemptsToTry)
	if err != nil {
		fmt.Println("Failed to heal the file")
		log.Println(err)
		return
	}

	fmt.Println("\n+++ <<-- Success! -->> +++")
	fmt.Println("Now you can successfully run " + healedFilename)
}
