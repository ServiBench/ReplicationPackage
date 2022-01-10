package core

import "context"

type IDRequest struct {
	ID string `json:"id"`
}

func Get(ctx context.Context, req IDRequest, repo Repository) (*ToDoItem, error) {
	if err := repo.Init(); err != nil {
		return nil, err
	}

	return repo.Get(ctx, req.ID)
}
