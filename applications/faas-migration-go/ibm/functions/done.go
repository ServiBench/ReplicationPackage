package main

import (
	"encoding/json"
	"fmt"
	"github.com/anonymous/faas-migration-go/core"
	"github.com/anonymous/faas-migration-go/ibm"
	"os"
)

func main() {
	arg := os.Args[1]

	fmt.Println(arg)
	var obj core.IDRequest
	json.Unmarshal([]byte(arg), &obj)
	if len(obj.ID) == 0 {
		ibm.SendError(fmt.Sprintf("An ID has to be defined!"), 400)
	}
	var pobj ibm.Obejct
	json.Unmarshal([]byte(arg), &pobj)
	repo := ibm.NewCloudantRepository(pobj)

	item, err := core.Done(nil, obj,repo)
	if err != nil {
		fmt.Printf("Execution Failed: Error %s\n", err.Error())
		ibm.SendError(fmt.Sprintf("Server Error: %s", err.Error()), 404)
	}
	res, _ := json.Marshal(ibm.Obejct{
		"statusCode": 200,
		"headers": ibm.Obejct{
			"Content-Type": "application/json",
		},
		"body": item,
	})

	fmt.Println(string(res))
}
