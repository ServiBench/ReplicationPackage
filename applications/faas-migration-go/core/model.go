package core

type ToDoItem struct {
	ID                 string `json:"ID"`
	Title              string `json:"title"`
	Description        string `json:"description"`
	InsertionTimestamp int64  `json:"insertion_timestamp"`
	DoneTimestamp      int64  `json:"done_timestamp"`
	Done               bool   `json:"done"`
}
