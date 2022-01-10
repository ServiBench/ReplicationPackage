package core

import "context"

func Delete(ctx context.Context, req IDRequest, repo Repository) error {
	if err := repo.Init(); err != nil {
		return err
	}

	_, err := repo.Get(ctx, req.ID)
	if err != nil {
		return err
	}

	return repo.Delete(ctx, req.ID)
}
