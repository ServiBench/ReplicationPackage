# Change this to the name of the bucket if The 'yq' command
# is not installed!
S3_BUCKET_NAME := `yq r serverless.yml 'custom.data_bucket_name'`

build: clean
	dotnet restore
	dotnet lambda package --configuration release --framework netcoreapp3.1 --output-package bin/release/netcoreapp3.1/matrix-mul.zip
	# Reinstall node_modules
	npm install

clean:
	# Remove Node Modules to prevent compilation issues
	rm -rvf node_modules || true
	rm -rvf bin/
	rm -rvf obj/

deploy: build
	serverless deploy -v

destroy:
	# Ensuring the bucket is empty
	aws s3 rm s3://$(S3_BUCKET_NAME) --recursive
	serverless remove -v
	