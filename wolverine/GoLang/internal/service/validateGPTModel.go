package service

import (
	"wolverine/pkg/request"
)

func ValidateGPTModel(apiKey string, model string) bool {
	modelsList, err := request.ModelsList(apiKey)
	// if something went wrong due to requesting the list -> acts like invalid inp
	if err != nil {
		return false
	}

	// looking for the model
	for _, m := range modelsList {
		if m.Id == model {
			return true
		}
	}

	return false
}
