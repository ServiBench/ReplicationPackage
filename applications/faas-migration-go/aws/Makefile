# Modify go Compilation Flags
GOFLAGS := -v

build:
	env GOOS=linux GO111MODULES=on go build $(GOFLAGS) -ldflags="-s -w" -o bin/put put/main.go
	env GOOS=linux GO111MODULES=on go build $(GOFLAGS) -ldflags="-s -w" -o bin/get get/main.go
	env GOOS=linux GO111MODULES=on go build $(GOFLAGS) -ldflags="-s -w" -o bin/del del/main.go
	env GOOS=linux GO111MODULES=on go build $(GOFLAGS) -ldflags="-s -w" -o bin/lst lst/main.go
	env GOOS=linux GO111MODULES=on go build $(GOFLAGS) -ldflags="-s -w" -o bin/done done/main.go

clean:
	rm -rf ./bin

deploy: clean build
	sls deploy --verbose

destroy:
	sls remove --verbose
