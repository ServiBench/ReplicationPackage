package ibm

import (
	"encoding/json"
	"fmt"
	"os"
)

func SendError(message string, code int) {
	obj, _ := json.Marshal(Obejct{
		"statusCode": code,
		"headers": Obejct{
			"Content-Type": "application/json",
		},
		"body": Obejct{
			"error": message,
			"ok":    false,
		},
	})
	fmt.Println(string(obj))
	os.Exit(1)
}
