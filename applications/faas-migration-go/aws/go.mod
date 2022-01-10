module github.com/anonymous/faas-migration-go/aws

go 1.12

require (
	github.com/aws/aws-lambda-go v1.8.2
	github.com/aws/aws-sdk-go v1.17.12
	github.com/aws/aws-xray-sdk-go v1.2.0
	github.com/gofrs/uuid v3.2.0+incompatible // indirect
	github.com/google/uuid v1.1.1
	github.com/guregu/dynamo v1.1.0
	github.com/anonymous/faas-migration-go/core v0.0.0-00010101000000-000000000000
)

replace github.com/anonymous/faas-migration-go/core => ../core
