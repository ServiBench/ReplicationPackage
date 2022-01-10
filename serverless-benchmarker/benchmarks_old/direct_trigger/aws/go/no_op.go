package main

import (
	"context"
	"fmt"
	"time"

	"github.com/aws/aws-lambda-go/lambda"
)

type GenericEvent struct {
	Name string `json:"name"`
}

func HandleRequest(ctx context.Context, name GenericEvent) (returnString string, err error) {
	currentTime := time.Now()
	returnString = fmt.Sprintf("Current time = %v\n", currentTime)

	return returnString, nil
}

func main() {
	lambda.Start(HandleRequest)
}
