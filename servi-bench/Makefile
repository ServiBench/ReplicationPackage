.PHONY: install sb_test lint test unit_test integration_test docker_build docker_debug

BENCH?=./tests/fixtures/mock_benchmark/mock_benchmark.py

all: sb_test

install:
	pip install --editable .[dev]

sb_test:
	sb test --file=${BENCH} --debug

lint:
	flake8 .

test: unit_test integration_test

unit_test:
	pytest tests/unit

integration_test:
	pytest tests/integration

docker_build:
	docker build -t serverless-benchmarker .

docker_debug:
	docker run --rm -it serverless-benchmarker /bin/bash
