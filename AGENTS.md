# Agent Environment

You are running as an OpenCode agent inside a Linux Docker container.

## Working Environment

- Your working directory is `/workspace`.
- The development website is available at `http://host.docker.internal:3000/`.
- `host.docker.internal` is the Docker hostname used to access services running on the host machine.

## Available Tools

- You have access to OpenCode's Bash, Read, Write, Edit, and WebFetch tools.
- Use the Bash tool to execute shell commands.
- When asked to run `curl`, execute the actual command using the Bash tool.
- Use WebFetch when explicitly requested.

## Task Execution

- Follow the user's task instructions.
- When asked to inspect a website, retrieve its contents using the requested tool.
- Do not assume local network addresses are inaccessible. Attempt the requested operation and report any errors.
- Do not claim a tool is unavailable without checking the tools provided in your environment.
