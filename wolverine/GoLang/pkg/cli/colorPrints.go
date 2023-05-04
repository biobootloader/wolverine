package cli

import (
	"fmt"
	"github.com/fatih/color"
)

func PrintRed(message string) {
	fmt.Println("  ")
	color.Red(message)
	fmt.Println("  ")
}

func PrintGreen(message string) {
	fmt.Println("  ")
	color.Green(message)
	fmt.Println("  ")
}

func PrintYellow(message string) {
	fmt.Println("  ")
	color.Yellow(message)
	fmt.Println("  ")
}
