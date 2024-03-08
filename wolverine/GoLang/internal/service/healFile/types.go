package healFile

type Request struct {
	Model     string `json:"model"`
	Prompt    string `json:"prompt"`
	MaxTokens int    `json:"max_tokens"`
}

type Response struct {
	Model   string `json:"model"`
	Choices []struct {
		Text         string `json:"text"`
		FinishReason string `json:"finish_reason"`
	} `json:"choices"`
	Usage struct {
		PromptTokens     int `json:"prompt_tokens"`
		CompletionTokens int `json:"completion_tokens"`
		TotalTokens      int `json:"total_tokens"`
	} `json:"usage"`
}

type GPTExplanation struct {
	Id       int      `json:"id"`
	Messages []string `json:"messages"`
}

type GPTAction struct {
	Id         int            `json:"id"`
	Operations []GPTOperation `json:"operations"`
}
type GPTOperation struct {
	Operation string `json:"operation"`
	Line      int    `json:"line"`
	Content   string `json:"content"`
}

type GPTResponse struct {
	Explanations []GPTExplanation `json:"explanations"`
	Actions      []GPTAction      `json:"actions"`
}

const DeleteOperationType = "Delete"
const InsertOperationType = "InsertAfter"
const ReplaceOperationType = "Replace"
