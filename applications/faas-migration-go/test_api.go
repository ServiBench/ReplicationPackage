package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io/ioutil"
	"math/rand"
	"net/http"
	"os"
	"strings"
	"time"
)

// -----------------------------------------------------------------------------
// Input Configuration
// -----------------------------------------------------------------------------

var (
	endpoint = flag.String("endpoint", "undefined", "The endpoint to the ToDo API implementation")
	count    = flag.Int("count", 50, "The number of items to insert.")
)

func init() {
	flag.Parse()
}

// -----------------------------------------------------------------------------
// Model Definitions
// -----------------------------------------------------------------------------

// This type defines the input object used to create a ToDo Item
type InsertRequest struct {
	Title       string `json:"title"`
	Description string `json:"description"`
}
type ToDoItem struct {
	ID                 string `json:"ID"`
	Title              string `json:"title"`
	Description        string `json:"description"`
	InsertionTimestamp int64  `json:"insertion_timestamp"`
	DoneTimestamp      int64  `json:"done_timestamp"`
}

// -----------------------------------------------------------------------------
// API Interactions
// -----------------------------------------------------------------------------

type api string

// Request all items from the api
func (endpoint api) ListItems() ([]ToDoItem, error) {
	res, err := http.Get(fmt.Sprintf("%slst", endpoint))
	if err != nil {
		return nil, err
	}
	// Best Practice: Close body when Function is done...
	defer res.Body.Close()

	data, err := ioutil.ReadAll(res.Body)
	if err != nil {
		return nil, err
	}
	var output []ToDoItem
	err = json.Unmarshal(data, &output)
	if err != nil {
		return nil, fmt.Errorf("Contents: %s Original Error: %s", string(data), err.Error())
	}

	return output, nil
}

func (endpoint api) InsertItem(i InsertRequest) (*ToDoItem, error) {
	data, err := json.Marshal(i)
	if err != nil {
		return nil, err
	}

	res, err := http.Post(fmt.Sprintf("%sput", endpoint), "application/json", bytes.NewReader(data))
	if err != nil {
		return nil, err
	}
	// Best Practice: Close body when Function is done...
	defer res.Body.Close()

	resdata, err := ioutil.ReadAll(res.Body)
	if err != nil {
		return nil, err
	}

	var item ToDoItem
	err = json.Unmarshal(resdata, &item)
	if err != nil {
		return nil, fmt.Errorf("Contents: %s Original Error: %s", string(data), err.Error())
	}

	return &item, nil
}

func (endpoint api) MarkAsDone(id string) error {
	res, err := http.Post(fmt.Sprintf("%sdone?id=%s", endpoint, id), "application/json", bytes.NewReader([]byte{}))
	if err != nil {
		return err
	}
	defer res.Body.Close()
	if res.StatusCode == 200 {
		return nil
	}
	return errors.New(fmt.Sprintf("API returned status code: %d instead of 200", res.StatusCode))
}
func (endpoint api) DeleteItem(id string) error {
	res, err := http.Post(fmt.Sprintf("%sdel?id=%s", endpoint, id), "application/json", bytes.NewReader([]byte{}))
	if err != nil {
		return err
	}
	defer res.Body.Close()
	if res.StatusCode == 200 {
		return nil
	}
	return errors.New(fmt.Sprintf("API returned status code: %d instead of 200", res.StatusCode))
}

func (endpoint api) GetItem(s string) (*ToDoItem, error) {
	res, err := http.Get(fmt.Sprintf("%sget?id=%s", endpoint, s))
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()
	if res.StatusCode != 200 {
		return nil, errors.New(fmt.Sprintf("API returned status code: %d instead of 200", res.StatusCode))
	}
	data, err := ioutil.ReadAll(res.Body)
	if err != nil {
		return nil, err
	}
	var item ToDoItem
	err = json.Unmarshal(data, &item)
	if err != nil {
		return nil, fmt.Errorf("Contents: %s Original Error: %s", string(data), err.Error())
	}
	return &item, nil
}

// -----------------------------------------------------------------------------
// Main Method
// -----------------------------------------------------------------------------

func main() {
	appUrl := *endpoint
	if appUrl == "undefined" {
		fmt.Println("The -endpoint Flag is required!")
		os.Exit(1)
	}
	// Append Trailing / if it is missing
	if !strings.HasSuffix(appUrl, "/") {
		appUrl += "/"
	}
	api := api(appUrl)
	api.CheckAvailability()
	items := api.InsertItems()
	api.CheckListItems(items, true, false)
	bound := (*count)/2
	fmt.Printf("Using Bound %d\n",bound)
	doneItems := items[:bound]
	notDoneItems := items[bound:]
	api.MarkItemsAsDone(doneItems)
	api.CheckListItems(doneItems, true, true)
	api.CheckItemsNotDone(notDoneItems)
	api.CheckDelete(items)
	api.CheckListItems(items, false, false)
	api.CheckFunctionsNotFoundBehaviour()
	fmt.Println("Success! All Checks have passed!")
}

// -----------------------------------------------------------------------------
// Tests
// -----------------------------------------------------------------------------

func (endpoint api) CheckAvailability() {
	// Call list to check if API is up
	fmt.Printf("Checking if API is Available....")
	_, err := endpoint.ListItems()
	if err != nil {
		fmt.Printf("Fail!\n")
		fmt.Printf("Ping API by calling List has Failed!\nError: %s\n", err.Error())
		os.Exit(1)
	}
	fmt.Printf("Ok!\n")
}

func (endpoint api) InsertItems() []ToDoItem {
	fmt.Printf("Inserting %d ToDo Items...", *count)
	insertionRequests := make([]InsertRequest, 0)
	items := make([]ToDoItem, 0)
	for i := 0; i < *count; i++ {
		ireq := InsertRequest{
			Title:       fmt.Sprintf("Todo-Item-#%d", i),
			Description: GenerateRandomString(300),
		}
		insertionRequests = append(insertionRequests, ireq)

		item, err := endpoint.InsertItem(ireq)
		if err != nil {
			fmt.Printf("Fail!\nError: %s\n", err.Error())
			os.Exit(1)
		}
		items = append(items, *item)
	}
	fmt.Printf("Done!\nValidating Responses....")
	if len(items) != len(insertionRequests) {
		fmt.Printf("Fail!\nResponse Count is not equal to Request Count\n")
		os.Exit(1)
	}
	for k, req := range insertionRequests {
		res := items[k]
		if res.Title != req.Title {
			if len(items) != len(insertionRequests) {
				fmt.Printf("Fail!\nA Title Did not match\n")
				os.Exit(1)
			}
		}
		if res.Description != req.Description {
			if len(items) != len(insertionRequests) {
				fmt.Printf("Fail!\nA Description Did not match\n")
				os.Exit(1)
			}
		}
	}
	fmt.Printf("Done!\n")
	return items
}

func (endpoint api) CheckListItems(items []ToDoItem, mustExist bool, checkIsDone bool) {
	fmt.Printf("Requesting List of Items...")
	itemsFromApp, err := endpoint.ListItems()
	if err != nil {
		fmt.Printf("Fail!\nError: %s\n", err.Error())
		os.Exit(1)
	}
	fmt.Printf("Done!\nSearching for inserted items...")
	for _, item := range items {
		found := false
		for _, ifa := range itemsFromApp {
			if ifa.ID == item.ID && ifa.Title == item.Title &&
				ifa.Description == item.Description {
				found = true
				if checkIsDone && ifa.DoneTimestamp == -1 {
					fmt.Printf("Fail!\nFound item that is expected to be Done but is not!\n")
					os.Exit(1)
				}
				break
			}
		}
		if !found && mustExist {
			fmt.Printf("Fail!\nCould not find an Item!\n")
			os.Exit(1)
		}
		if found && !mustExist {
			fmt.Printf("Fail!\nFound Item that should be deleted!!\n")
			os.Exit(1)
		}
	}
	fmt.Printf("Done!\n")
}

func (endpoint api) MarkItemsAsDone(items []ToDoItem) {
	fmt.Printf("Marking %d items as Done...", len(items))

	for _, item := range items {
		err := endpoint.MarkAsDone(item.ID)
		if err != nil {
			fmt.Printf("Fail!\nError: %s\n", err.Error())
			os.Exit(1)
		}
	}

	fmt.Printf("Done!\n")
}

func (endpoint api) CheckItemsNotDone(items []ToDoItem) {
	fmt.Printf("Using 'Get' Function to check if the %d items are Done...", len(items))

	for _, item := range items {
		i, err := endpoint.GetItem(item.ID)
		if err != nil {
			fmt.Printf("Fail!\nError: %s\n", err.Error())
			os.Exit(1)
		}
		if i.ID != item.ID {
			fmt.Printf("Fail!\nGet Item returned a different ID then queried.\n")
			os.Exit(1)
		}
		if i.DoneTimestamp != -1 {
			fmt.Printf("Fail!\nAn Item is marked as done while it should not!\n")
			os.Exit(1)
		}
	}

	fmt.Printf("Done!\n")
}

func (endpoint api) CheckDelete(items []ToDoItem) {
	fmt.Printf("Deleting all inserted Items...")
	for _, item := range items {
		err := endpoint.DeleteItem(item.ID)
		if err != nil {
			fmt.Printf("Fail!\nError: %s\n", err.Error())
			os.Exit(1)
		}
	}
	fmt.Printf("Done!\n")
}

func (endpoint api) CheckFunctionsNotFoundBehaviour() {
	fmt.Println("Checking ID specific functions API Behaviour if ID does not exist")
	fmt.Printf("Get Function...")
	_, err := endpoint.GetItem(NotFoundTestGuid)
	if err == nil {
		fmt.Printf("Fail!\nExpected Error. Got None.\n")
		os.Exit(1)
	}
	fmt.Printf("Ok! Got error: %s\nDone Function...", err.Error())
	err = endpoint.MarkAsDone(NotFoundTestGuid)
	if err == nil {
		fmt.Printf("Fail!\nExpected Error. Got None.\n")
		os.Exit(1)
	}
	fmt.Printf("Ok! Got error: %s\nDelete Function...", err.Error())
	err = endpoint.DeleteItem(NotFoundTestGuid)
	if err == nil {
		fmt.Printf("Fail!\nExpected Error. Got None.\n")
		os.Exit(1)
	}
	fmt.Printf("Ok Got error: %s!\n", err.Error())
}

// -----------------------------------------------------------------------------
// Utility Methods
// -----------------------------------------------------------------------------

const NotFoundTestGuid = "8324cf72-84c6-4001-bec2-46505dbe4301"

const randomStringCharset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

var charsetRunes []rune

func init() {
	charsetRunes = bytes.Runes([]byte(randomStringCharset))
	rand.Seed(time.Now().Unix())
}

func GenerateRandomString(l int) string {
	id := ""
	for i := 0; i < l; i++ {
		idx := rand.Intn(len(charsetRunes))
		id += string(charsetRunes[idx])
	}
	return id
}
