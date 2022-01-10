# ToDo API

This Directory contains the implementations of the ToDo API on Microsoft Azure. The other implementations are based on Go and can be found under
https://github.com/iaas-splab/faas-migration-go

## Running the Tests

To run the tests, esure the Go SDK is installed. After that the tests can be executed by running the following command in this directory:
```
go run *.go -endpoint <API Endpoint> -count <Count>
```

The tests assume the implemeńtation you want to test is already deployed. To do so follow the instructions in the directories of the
implementations.

the `count` flag sets the number of items this test should insert. It is recomended that this value is dividable by 2 because half of these items
will be marked as done during the test. (default is 50)

### IBM Note

Due to the rate limits on the Lite plan on the Cloudant service the IBM implementation only supports a small `count` value. Tests have shown that Values below 10 work without issues however more requests will be rate limited causing functions to fail. To fix this a Cloudant Service with a larger service plan like standard has to be created.

## API Specification

The ToDo API Consists of the following functions:

- `POST /put`: Submit an Item to the API
- `GET /get`: Get an Item
- `GET /lst`: List all Items
- `POST /done`: Mark an Item as Done
- `POST /del`: Delete an Item

All Methods produce JSON responses and accept JSON requests.

### `/put` Function

The `/put` function consumes an ItemCreation Request as JSON and returns a ToDo Item with an ID as a JSON Response.

It can produce the following HTTP status codes:
- 200: Item was pushed successfuly
- 400: Invalid Input
- 500: Server Error

No Query Parameters are set.

### `/lst` Function

Returns a JSON array of all ToDO items in the database. The Returned body is a JSON array.

This function Produces the following status codes:
- 200: Sucess, the Item is the returned body
- 500: Server Error

### `/get` Function

Returns a specific ToDo Item based on the `id` query parameter. This parameter defines the id of the item that sould be looked for.

This function Produces the following status codes:
- 200: Sucess, the Item is the returned body
- 400: The `id` is not set
- 404: The given ID was invalid

### `/del` Function

Deletes a specific ToDo Item based on the `id` query parameter. This parameter defines the id of the item that sould be looked for.

The body this function has to return is not defined.

This function Produces the following status codes:
- 200: Sucess, the Item was deleted
- 400: The `id` is not set
- 404: The given ID was invalid

### `/done` Function

Marks a a specific ToDo Item as done based on the `id` query parameter. This parameter defines the id of the item that sould be looked for.

The body this function has to return is not defined.

This function Produces the following status codes:
- 200: Sucess, the Item was deleted
- 400: The `id` is not set
- 404: The given ID was invalid
The `/put` function consumes an ItemCreation Request

### ToDo Item

```json
{
  "ID": "8c299858-4bf0-4b2d-89ea-36bd5dc09fde",
  "title": "MyTitle",
  "description": "MyDescription",
  "insertion_timestamp": 1566323969,
  "done_timestamp": -1
}
```

- `ID`:The ID of the inserted element. This does not have to be a Guid
- `title`: The tile of the Item to insert
- `description`: The description of the message
- `insertion_timestamp`: The unix timestamp of the time when the event was inserted into the database
- `done_timestamp`: The Timestamp at which the item was marked as done. If the value is -1 the item is not marked as done.

### ItemCreation Request

```json
{
  "title": "MyTitle",
  "description": "MyDescription"
}
```

- `title`: The tile of the Item to insert (Required)
- `description`: The description of the message (Required)
