package core

import "context"

func List(ctx context.Context, repo Repository) ([]ToDoItem, error) {
	if err := repo.Init(); err != nil {
		return nil, err
	}

	return repo.List(ctx)
}
