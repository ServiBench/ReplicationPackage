package main

import (
	"bytes"
	"encoding/json"
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
	delay    = flag.Int("delay", 90, "The delay, in seconds, between insertion and validation")
	count    = flag.Int("count", 50, "Number of events per type to insert")
)

func init() {
	flag.Parse()
}

// -----------------------------------------------------------------------------
// Model Definitions
// -----------------------------------------------------------------------------

type ProcessedEvent struct {
	ID        int    `json:"ID"`
	Source    string `json:"source"`
	Timestamp int64  `json:"timestamp"`
	Message   string `json:"message"`
}

type BaseEvent struct {
	Type      string `json:"type"`
	Source    string `json:"source"`
	Timestamp int    `json:"timestamp"`
}

type TemperatureEvent struct {
	BaseEvent
	Value int `json:"value"`
}

type ForecastEvent struct {
	BaseEvent
	Forecast    int    `json:"forecast"`
	ForecastFor string `json:"forecast_for"`
	Place       string `json:"place"`
}

type StateChangeEvent struct {
	BaseEvent
	Message string `json:"message"`
}

// -----------------------------------------------------------------------------
// API Definitions
// -----------------------------------------------------------------------------

type api string

func (a api) ListEvents() ([]ProcessedEvent, error) {
	res, err := http.Get(fmt.Sprintf("%slist", a))
	if err != nil {
		return nil, err
	}
	// Best Practice: Close body when Function is done...
	defer res.Body.Close()

	data, err := ioutil.ReadAll(res.Body)
	if err != nil {
		return nil, err
	}
	var output []ProcessedEvent
	err = json.Unmarshal(data, &output)
	if err != nil {
		return nil, err
	}

	return output, nil
}

func (a api) GetLatest() (*ProcessedEvent, error) {
	res, err := http.Get(fmt.Sprintf("%slatest", a))
	if err != nil {
		return nil, err
	}
	// Best Practice: Close body when Function is done...
	defer res.Body.Close()

	data, err := ioutil.ReadAll(res.Body)
	if err != nil {
		return nil, err
	}
	var output []ProcessedEvent
	err = json.Unmarshal(data, &output)
	if err != nil {
		return nil, err
	}

	if len(output) != 1 {
		return nil, nil
	}

	return &output[0], nil
}

func (a api) InsertStateChangeEvent(i StateChangeEvent) error {
	data, err := json.Marshal(i)
	if err != nil {
		return err
	}

	res, err := http.Post(fmt.Sprintf("%singest", a), "application/json", bytes.NewReader(data))
	if err != nil {
		return err
	}
	// Best Practice: Close body when Function is done...
	defer res.Body.Close()

	_, err = ioutil.ReadAll(res.Body)
	if err != nil {
		return err
	}

	return nil
}

func (a api) InsertForecastEvent(i ForecastEvent) error {
	data, err := json.Marshal(i)
	if err != nil {
		return err
	}

	res, err := http.Post(fmt.Sprintf("%singest", a), "application/json", bytes.NewReader(data))
	if err != nil {
		return err
	}
	// Best Practice: Close body when Function is done...
	defer res.Body.Close()

	_, err = ioutil.ReadAll(res.Body)
	if err != nil {
		return err
	}

	return nil
}

func (a api) InsertTemperatureEvent(i TemperatureEvent) error {
	data, err := json.Marshal(i)
	if err != nil {
		return err
	}

	res, err := http.Post(fmt.Sprintf("%singest", a), "application/json", bytes.NewReader(data))
	if err != nil {
		return err
	}
	// Best Practice: Close body when Function is done...
	defer res.Body.Close()

	_, err = ioutil.ReadAll(res.Body)
	if err != nil {
		return err
	}

	return nil
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
	api.CheckEndpoint()
	evts := api.InsertEvents()
	fmt.Printf("Waiting %d Seconds to let the events process...\n", *delay)
	for i := 1; i <= *delay; i++ {
		fmt.Printf("\r%03d Seconds Remaining....", *delay-i)
		time.Sleep(time.Second)
	}
	fmt.Println()
	api.ValidateEventsInserted(evts)
	api.TestLatest()
	fmt.Println("Test Execution Done!")
}

// -----------------------------------------------------------------------------
// Tests
// -----------------------------------------------------------------------------

func (a api) CheckEndpoint() {
	fmt.Printf("Checking Connectivity to Endpoint by the List Function....")
	_, err := a.ListEvents()
	if err != nil {
		fmt.Printf("Fail!\nError: %s\n", err.Error())
		os.Exit(1)
	}
	fmt.Println("Ok!")
}

func (a api) InsertEvents() []BaseEvent {
	fmt.Println("Inserting Events...")
	evts := make([]BaseEvent, 0)
	fmt.Printf("Inserting %d Temperature Events...", *count)
	for i := 0; i < *count; i++ {
		temperatureEvent := TemperatureEvent{
			BaseEvent: BaseEvent{
				Type:      "temperature",
				Source:    GenerateRandomString(30),
				Timestamp: int(time.Now().Unix() / 1000),
			},
			Value: rand.Intn(200),
		}
		err := a.InsertTemperatureEvent(temperatureEvent)
		if err != nil {
			fmt.Printf("Fail!\nError: %s\n", err.Error())
			os.Exit(1)
		}
		evts = append(evts, temperatureEvent.BaseEvent)
	}
	fmt.Println("Ok!")
	fmt.Printf("Inserting %d Forecast Events...", *count)
	for i := 0; i < *count; i++ {
		forecastEvent := ForecastEvent{
			BaseEvent: BaseEvent{
				Type:      "forecast",
				Source:    GenerateRandomString(30),
				Timestamp: int(time.Now().Unix() / 1000),
			},
			Forecast:    rand.Intn(200),
			ForecastFor: GenerateRandomString(10),
			Place:       GenerateRandomString(10),
		}
		err := a.InsertForecastEvent(forecastEvent)
		if err != nil {
			fmt.Printf("Fail!\nError: %s\n", err.Error())
			os.Exit(1)
		}
		evts = append(evts, forecastEvent.BaseEvent)
	}
	fmt.Println("Ok!")
	fmt.Printf("Inserting %d State Change Events...", *count)
	for i := 0; i < *count; i++ {
		stateChangeEvent := StateChangeEvent{
			BaseEvent: BaseEvent{
				Type:      "state_change",
				Source:    GenerateRandomString(30),
				Timestamp: int(time.Now().Unix() / 1000),
			},
			Message: GenerateRandomString(30),
		}
		err := a.InsertStateChangeEvent(stateChangeEvent)
		if err != nil {
			fmt.Printf("Fail!\nError: %s\n", err.Error())
			os.Exit(1)
		}
		evts = append(evts, stateChangeEvent.BaseEvent)
	}
	fmt.Println("Ok!")

	return evts
}

func (a api) ValidateEventsInserted(events []BaseEvent) {
	fmt.Printf("Retrieving all events from the database...")
	evts, err := a.ListEvents()
	if err != nil {
		fmt.Printf("Fail!\nError: %s\n", err.Error())
		os.Exit(1)
	}
	fmt.Println("Ok!")
	fmt.Print("Validating that all events have been processed...")
	fail := false
	notFoundCount := 0
	for _, event := range events {
		found := false
		for _, processedEvent := range evts {
			if processedEvent.Source == event.Source {
				found = true

				if event.Type == "state_change" && !strings.Contains(processedEvent.Message, "status") {
					fmt.Printf("Fail!\nMessage Processing of State Change Message Failed\n")
					os.Exit(1)
				}
				if event.Type == "forecast" && !strings.Contains(processedEvent.Message, "Forecasted") {
					fmt.Printf("Fail!\nMessage Processing of Forecast Message Failed\n")
					os.Exit(1)
				}
				if event.Type == "temperature" && !strings.Contains(processedEvent.Message, "Temperature") {
					fmt.Printf("Fail!\nMessage Processing of Temperature Message Failed\n")
					os.Exit(1)
				}

				break
			}
		}
		if !found {
			fail = true
			notFoundCount++
		}
	}
	if fail {
		fmt.Println("Warning!")
		failPerc := float64(notFoundCount) / float64(len(events))
		fmt.Printf("%03d of %03d (%f%%) insertions were not found!\n", notFoundCount, len(events), failPerc)
		return
	}
	fmt.Println("Ok!")
}

func (a api) TestLatest() {
	fmt.Printf("Fetching latest element...")
	e, err := a.GetLatest()
	if err != nil {
		fmt.Printf("Fail!\nError: %s\n", err.Error())
		os.Exit(1)
	}
	fmt.Printf("Ok! Got ID %d\n", e.ID)
}

// -----------------------------------------------------------------------------
// Utility Methods
// -----------------------------------------------------------------------------

const randomStringCharset = "abcdefghijklmnopqrstuvwxyz"

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
