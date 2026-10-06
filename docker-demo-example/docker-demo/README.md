# docker-demo: office hours walkthrough

1. `docker --version` and `make --version` (tools installed?)
2. `make run`, then open http://localhost:8000 (image -> container, port mapping)
3. With it running, edit the message in `app.py`, save, refresh (bind mount + debug reload)
4. `docker ps` in a 2nd terminal (see the running container); Ctrl+C to stop
5. `make shell`, then `ls` and `exit` (you're inside the container; files are the same ones as on your laptop)
6. `make test`
7. `claude` in this folder: "add a /about route with a test". Show CLAUDE.md, .claude/settings.json, and `/test`.

Files: Dockerfile = recipe, Makefile = shortcuts, CLAUDE.md = instructions for Claude,
.claude/settings.json = permissions, .claude/commands/ = custom slash commands.
