package healFile

import (
	"fmt"
	"os/exec"
)

func isCompilable(filename string, compileError *string) bool {
	cmd := exec.Command("go", "run", filename)
	output, err := cmd.CombinedOutput()
	if err != nil {
		*compileError = string(output)
		fmt.Println("The file contains compile errors:")
		fmt.Println(*compileError)

		fmt.Printf("\nWait for our brainstorm outcome...\n\n")
	}

	return err == nil
}
