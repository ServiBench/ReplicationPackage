package core

import (
	"context"
	"time"
)

type PutRequest struct {
	Title       string `json:"title"`
	Description string `json:"description"`
}

type PutResponse struct {
	Key string `json:"key"`
}

func Put(ctx context.Context, req PutRequest, repo Repository) (*ToDoItem, error) {
	if err := repo.Init(); err != nil {
		return nil, err
	}

	i := ToDoItem{
		Title:              req.Title,
		Description:        req.Description,
		Done:               false,
		InsertionTimestamp: time.Now().Unix(),
		DoneTimestamp:      -1,
	}

	if _, err := repo.Put(ctx, &i); err != nil {
		return nil, err
	}

	return &i, nil
}
