module github.com/anonymous/faas-migration-go/ibm

go 1.12

require (
	github.com/cloudant-labs/go-cloudant v0.0.0-20180620160115-81a70ee15c97
	github.com/anonymous/faas-migration-go/core v0.0.0-00010101000000-000000000000
)

replace github.com/anonymous/faas-migration-go/core => ../core
