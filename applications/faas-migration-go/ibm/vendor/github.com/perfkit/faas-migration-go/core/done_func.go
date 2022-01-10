package core

import (
	"context"
	"time"
)

func Done(ctx context.Context, req IDRequest, repo Repository) (*ToDoItem, error) {
	if err := repo.Init(); err != nil {
		return nil, err
	}

	item, err := repo.Get(ctx, req.ID)
	if err != nil {
		return nil, err
	}

	item.Done = true
	item.DoneTimestamp = time.Now().Unix()

	return repo.Put(ctx, item)
}
