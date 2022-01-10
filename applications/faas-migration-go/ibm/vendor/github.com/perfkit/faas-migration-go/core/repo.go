package core

import "context"

type Repository interface {
	// This method is meant to initialize the connection between the Function and the database
	// an error should be returned if the connection fails.
	Init() error
	// This Method stores a given object which is never nil in the database.
	// The object returned should be identical to the one inserted but with an id assigned
	// to it by the database or using the implementation if the element is inserted for the first time.
	// However this method is also used to update the ToDoItems when they are marked as done. It therefore must be ensured
	// that an ID is only created if the element is new. This is the case if the ID of the input todo item is either nil or
	// has length 0. It is not required to use the same memory address
	// therefore a new instance of the ToDoItem Struct can be created with the same values as the given one.
	// It the insertion fails this method should return an error and the first parameter should be nil
	Put(context.Context, *ToDoItem) (*ToDoItem, error)
	// This method attempts to retrieve a ToDoItem from the database based on the given ID
	// if there is an error for example if the id cannot be found or the database does not exists this
	// method should return an error and the first parameter should be nil.
	Get(context.Context, string) (*ToDoItem, error)
	// This method returns a list of all ToDoItems currently stored in the database. If no entries are found the array MUST
	// be empty and only if a unexpected error occurs the method shuld return an error. Then the first parameter shuld be nil
	List(context.Context) ([]ToDoItem, error)
	// This method attempts to delete a ToDoItem from the database based on the given ID
	// if there is an error for example if the id cannot be found or the database does not exists this
	// method should return an error and the first parameter should be nil.
	Delete(context.Context, string) error
}
