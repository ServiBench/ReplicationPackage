package ibm

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/cloudant-labs/go-cloudant"
	"github.com/anonymous/faas-migration-go/core"
)

type Obejct map[string]interface{}

const (
	CloudantEndpointParamName = "cloudant_host"
	CloudantUsernameParamName = "cloudant_username"
	CloudantPasswordParamName = "cloudant_password"
	CloudantDbNameParamName   = "cloudant_db_name"
)

var CloudantEndpoint = ""
var CloudantUserName = ""
var CloudantPassword = ""
var DatabaseName = ""

type cloudantItem struct {
	Id                 string        `json:"_id,omitempty"`
	Rev                string        `json:"_rev"`
	Title              string        `json:"title"`
	Description        string        `json:"description"`
	InsertionTimestamp int64         `json:"insertion_timestamp"`
	DoneTimestamp      int64         `json:"done_timestamp"`
	Done               bool          `json:"done"`
	Element            core.ToDoItem `json:"element"`
}

func NewCloudantRepository(data Obejct) core.Repository {
	d, _ := json.Marshal(data)
	fmt.Println(string(d))

	CloudantEndpoint = data[CloudantEndpointParamName].(string)
	CloudantUserName = data[CloudantUsernameParamName].(string)
	CloudantPassword = data[CloudantPasswordParamName].(string)
	DatabaseName = data[CloudantDbNameParamName].(string)

	repo := &cloudantRepository{}

	return core.Repository(repo)
}

type cloudantRepository struct {
	Client *cloudant.CouchClient
}

func (c *cloudantRepository) Init() error {
	client, err := cloudant.CreateClient(CloudantUserName, CloudantPassword, CloudantEndpoint, 5)
	if err != nil {
		fmt.Println(err.Error())
		return err
	}

	_, err = client.Get(DatabaseName)
	if err != nil {
		fmt.Println(err.Error())
		_, err = client.GetOrCreate(DatabaseName)
		if err != nil {
			fmt.Println(err.Error())
			return err
		}
	}

	c.Client = client
	return nil
}

func (i cloudantItem) toToDoItem() core.ToDoItem {
	return core.ToDoItem{
		ID:                 i.Id,
		InsertionTimestamp: i.InsertionTimestamp,
		DoneTimestamp:      i.DoneTimestamp,
		Done:               i.Done,
		Title:              i.Title,
		Description:        i.Description,
	}
}

func (c *cloudantRepository) Put(ctx context.Context, item *core.ToDoItem) (*core.ToDoItem, error) {
	id := item.ID
	rev := "2-xxxxxxx"

	e := cloudantItem{
		Id:                 id,
		Rev:                rev,
		Description:        item.Description,
		Title:              item.Title,
		Done:               item.Done,
		DoneTimestamp:      item.DoneTimestamp,
		InsertionTimestamp: item.InsertionTimestamp,
	}

	db, err := c.Client.Get(DatabaseName)
	if err != nil {
		return nil, err
	}

	if len(id) != 0 {
		var el cloudantItem

		err = db.Get(id, cloudant.NewGetQuery().Attachments().Latest().Build(), &el)
		if err != nil {
			return nil, err
		}

		e.Rev = el.Rev
	}
	meta, err := db.Set(&e)
	if err != nil {
		return nil, err
	}
	fmt.Printf("Inserted Element with id %s and rev %s\n", meta.ID, meta.Rev)
	item.ID = meta.ID

	return item, nil
}

func (c *cloudantRepository) Get(ctx context.Context, id string) (*core.ToDoItem, error) {
	db, err := c.Client.Get(DatabaseName)
	if err != nil {
		return nil, err
	}

	var e cloudantItem

	err = db.Get(id, cloudant.NewGetQuery().Attachments().Latest().Build(), &e)
	if err != nil {
		return nil, err
	}
	if len(e.Id) == 0 {
		return nil, fmt.Errorf("Returned ID is Zero!")
	}
	fmt.Printf("Got ID %s\n", e.Id)
	i := e.toToDoItem()
	return &i, nil
}

func (c *cloudantRepository) List(ctx context.Context) ([]core.ToDoItem, error) {
	db, err := c.Client.Get(DatabaseName)
	if err != nil {
		return nil, err
	}

	rows, err := db.All(cloudant.NewAllDocsQuery().Build())

	items := make([]core.ToDoItem, 0)

	for {
		row, more := <-rows
		if more {
			fmt.Println(row.ID, row.Value.Rev) // prints document 'id' and 'rev'
			elem, _ := c.Get(ctx, row.ID)
			items = append(items, *elem)
		} else {
			break
		}
	}

	return items, nil
}

func (c *cloudantRepository) Delete(ctx context.Context, id string) error {
	db, err := c.Client.Get(DatabaseName)
	if err != nil {
		return err
	}
	var el cloudantItem

	err = db.Get(id, cloudant.NewGetQuery().Attachments().Latest().Build(), &el)
	if err != nil {
		return err
	}

	return db.Delete(id, el.Rev)
}
