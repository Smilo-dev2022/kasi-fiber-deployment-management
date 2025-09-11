REGISTRY ?= ghcr.io
IMAGE ?= $(REGISTRY)/$(shell basename $$(git rev-parse --show-toplevel 2>/dev/null || echo app))
TAG ?= dev

.PHONY: help build push run harden

help:
	@echo "Targets: build, push, run, harden"

build:
	docker build -t $(IMAGE):$(TAG) .

push: build
	docker push $(IMAGE):$(TAG)

run:
	docker run --rm -it -p 8080:8080 $(IMAGE):$(TAG)

harden:
	bash scripts/harden_repo.sh

