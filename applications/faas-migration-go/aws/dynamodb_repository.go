package aws

import (
	"context"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/dynamodb"
	"github.com/aws/aws-xray-sdk-go/xray"
	"github.com/google/uuid"
	"github.com/guregu/dynamo"
	"github.com/perfkit/faas-migration-go/core"
	"os"
)

type Response events.APIGatewayProxyResponse
type Request events.APIGatewayProxyRequest

const TableNameEnvName = "DYNAMODB_TABLE"

var TableName = os.Getenv(TableNameEnvName)

type DynamoRepo struct {
	TableName string

	session *session.Session
	db      *dynamo.DB
	table   *dynamo.Table
}

func (r *DynamoRepo) Put(ctx context.Context, i *core.ToDoItem) (*core.ToDoItem, error) {
	if len(i.ID) == 0 {
		i.ID = uuid.New().String()
	}
	err := r.table.Put(*i).RunWithContext(ctx)
	if err != nil {
		return nil, err
	}
	return i, nil
}

func (r *DynamoRepo) Get(ctx context.Context, k string) (*core.ToDoItem, error) {
	var item core.ToDoItem
	err := r.table.Get("ID", k).OneWithContext(ctx, &item)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *DynamoRepo) List(ctx context.Context) ([]core.ToDoItem, error) {
	items := make([]core.ToDoItem, 0)

	err := r.table.Scan().AllWithContext(ctx, &items)
	if err != nil {
		return nil, err
	}

	return items, nil
}

func (r *DynamoRepo) Delete(ctx context.Context, k string) error {
	return r.table.Delete("ID", k).RunWithContext(ctx)
}

func NewDynamoRepo() core.Repository {
	return &DynamoRepo{
		TableName: TableName,
	}
}

func (r *DynamoRepo) Init() error {
	r.session = session.Must(session.NewSession())

	customClient := dynamodb.New(session.Must(session.NewSession()))
	xray.AWS(customClient.Client)
	r.db = dynamo.NewFromIface(customClient)

	/**r.db = dynamo.New(r.session)
	client := r.db.Client().(*dynamodb.DynamoDB).Client
	xray.AWS(client)**/

	table := r.db.Table(r.TableName)
	r.table = &table

	return nil
}
