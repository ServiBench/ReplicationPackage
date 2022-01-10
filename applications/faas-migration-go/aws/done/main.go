package main

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/anonymous/faas-migration-go/aws"
	"github.com/anonymous/faas-migration-go/core"
)

func Handler(ctx context.Context, req aws.Request) (aws.Response, error) {
	var elem core.IDRequest
	elem.ID = req.QueryStringParameters["id"]

	if elem.ID == "" {
		fmt.Printf("ID Missing\n")
		return aws.Response{
			StatusCode: 400,
			Headers: map[string]string{
				"Content-Type": "application/json",
			},
			Body: `{"message":"ID has to be supplied."}`,
		}, nil
	}

	fmt.Println("Submitted ID", elem.ID)

	r := aws.NewDynamoRepo()

	res, err := core.Done(ctx, elem, r)
	if err != nil {
		fmt.Printf("Done Failed %q", err.Error())
		return aws.Response{
			StatusCode: 404,
		}, err
	}

	d, err := json.Marshal(res)
	if err != nil {
		fmt.Printf("Response Marshal failed %q", err.Error())
		return aws.Response{
			StatusCode: 500,
		}, err
	}

	resp := aws.Response{
		StatusCode:      200,
		IsBase64Encoded: false,
		Body:            string(d),
		Headers: map[string]string{
			"Content-Type": "application/json",
		},
	}

	return resp, nil
}

func main() {
	lambda.Start(Handler)
}
