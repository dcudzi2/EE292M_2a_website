# docker-demo

Tiny Flask app used to teach Docker + Claude Code.

## Commands
- `make run`   build the image and start the app at http://localhost:8000
- `make test`  run pytest inside the container
- `make shell` open a bash shell inside the container

## Rules
- Run code and tests through `make`, not directly on the laptop.
- Keep changes small; update/add a test for each change.
- Do not edit the Dockerfile unless asked.
