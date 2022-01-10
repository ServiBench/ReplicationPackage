package main

import (
	"encoding/json"
	"fmt"
	"github.com/anonymous/faas-migration-go/core"
	"github.com/anonymous/faas-migration-go/ibm"
	"os"
)

func main() {
	fmt.Println(os.Args[1])
	var pobj ibm.Obejct
	json.Unmarshal([]byte(os.Args[1]), &pobj)
	repo := ibm.NewCloudantRepository(pobj)

	items, err := core.List(nil, repo)
	if err != nil {
		fmt.Printf("Execution Failed: Error %s\n", err.Error())
		ibm.SendError(fmt.Sprintf("Server Error: %s", err.Error()), 500)
	}

	res, _ := json.Marshal(ibm.Obejct{
		"statusCode": 200,
		"headers": ibm.Obejct{
			"Content-Type": "application/json",
		},
		"body": items,
	})

	fmt.Println(string(res))
}
