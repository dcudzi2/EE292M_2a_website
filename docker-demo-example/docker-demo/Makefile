# Usage: make build | make run | make test | make shell
IMAGE = docker-demo

build:
	docker build -t $(IMAGE) .

# -p: forward laptop port 8000 -> container port 8000
# -v: mount this folder into /app so edits on your laptop show up live
run: build
	docker run --rm -p 8000:8000 -v "$(CURDIR)":/app $(IMAGE)

test: build
	docker run --rm -v "$(CURDIR)":/app $(IMAGE) pytest

shell: build
	docker run --rm -it -v "$(CURDIR)":/app $(IMAGE) bash
