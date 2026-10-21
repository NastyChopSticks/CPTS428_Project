## Dependencies

Before running the project, ensure the following dependencies are installed.

### 1. Docker

Docker is required to run the containerized AI agent.

- **Windows / macOS:** Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
- **Linux:** Install [Docker Engine](https://docs.docker.com/engine/install/) and the [Docker Compose plugin](https://docs.docker.com/compose/install/linux/).

Ensure Docker is running before proceeding.

Verify the installation:

```bash
docker --version
docker compose version
docker info
```

### 2. WSL 2 (Windows Only)

Windows users running Linux containers through Docker Desktop should use the WSL 2 backend.

Install WSL 2 using PowerShell as Administrator:

```powershell
wsl --install
```

Restart your computer if prompted.

Verify the installation:

```powershell
wsl --status
```

In Docker Desktop, navigate to **Settings → General** and ensure **Use the WSL 2 based engine** is enabled.

**Note:** macOS and Linux users do not need WSL. Docker handles Linux container execution through its supported virtualization or container runtime.

### 3. Ollama and Qwen3

Install [Ollama](https://ollama.com/download) and download the required model:

```bash
ollama pull qwen3:4b-instruct
```

Verify the model is installed:

```bash
ollama list
```

#### Configure Context Window

For consistent testing, we use a context window of **16,384 tokens**.

Configure Ollama's default context length using the `OLLAMA_CONTEXT_LENGTH` environment variable.

**Windows (PowerShell):**

```powershell
[Environment]::SetEnvironmentVariable("OLLAMA_CONTEXT_LENGTH", "16384", "User")
```

Restart Ollama after changing this setting.

**macOS / Linux:**

If running Ollama manually:

```bash
OLLAMA_CONTEXT_LENGTH=16384 ollama serve
```

If Ollama is managed by systemd on Linux, follow the configuration below instead.

**Note:** OpenCode must also be configured with the appropriate model context limit. Increasing the context window increases memory usage.

#### Configure Ollama Networking and Context (Linux Only)

On Linux, Ollama may listen only on `127.0.0.1`, preventing Docker containers from connecting.

We configure Ollama to listen on the Docker bridge interface rather than all network interfaces. This also sets the context window to 16,384 tokens.

**1. Find the Docker bridge IP:**

```bash
ip -4 addr show docker0
```

Look for an address such as `172.17.0.1`.

**2. Configure Ollama:**

Replace `172.17.0.1` below if your Docker bridge uses a different address.

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
```

```bash
printf '[Service]\nEnvironment="OLLAMA_HOST=172.17.0.1:11434"\nEnvironment="OLLAMA_CONTEXT_LENGTH=16384"\n' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
```

**3. Restart Ollama:**

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

**4. Verify the listener:**

```bash
ss -ltnp | grep 11434
```

You should see Ollama listening on the Docker bridge address.

**5. Test Docker connectivity:**

From the directory containing `compose.yaml`:

```bash
docker compose run --rm --entrypoint /bin/sh opencode -c "curl -i http://host.docker.internal:11434/api/tags"
```

A successful connection should return HTTP `200 OK`.

**Important:** When Ollama listens only on the Docker bridge IP, local Ollama CLI commands may need the same address:

```bash
OLLAMA_HOST=172.17.0.1:11434 ollama list
```

This configuration assumes Ollama is installed as a systemd service. It reduces network exposure compared with binding to `0.0.0.0`, but does not provide authentication.

#### Windows and macOS Networking

Docker Desktop supports `host.docker.internal` for accessing services running on the host machine.

In most cases, no additional networking configuration is necessary. If OpenCode cannot connect to Ollama, verify the server is running and that the container can reach port `11434`.
**4. Verify the listener:**

```bash
ss -ltnp | grep 11434
```

You should see Ollama listening on the Docker bridge IP rather than `0.0.0.0`.

**5. Test Docker connectivity:**

From the directory containing `compose.yaml`:

```bash
docker compose run --rm --entrypoint /bin/sh opencode -c "curl -i http://host.docker.internal:11434/api/tags"
```

A successful connection should return an HTTP `200 OK` response.

**Note:** This configuration assumes Ollama runs as a systemd service and the Docker bridge IP is reachable from the container. It may also require configuring the Ollama CLI to use the bridge address instead of `localhost`.

Binding to the Docker bridge reduces network exposure, but it does not provide authentication. Keep the Docker environment and VM network restricted to trusted users.

#### Windows and macOS

Docker Desktop supports `host.docker.internal` for accessing host services. In most cases, no Ollama listener changes are necessary.

If the agent cannot connect, verify Ollama is running and test the API from inside Docker before changing network settings.

### 4. Node.js and npm

Node.js is required to run the Next.js development server. npm is included with Node.js.

Download and install the **LTS version** from [Node.js](https://nodejs.org/en/download).

Verify the installation:

```bash
node -v
npm -v
```

No separate installation of React or Next.js is necessary. Project dependencies are installed using npm.

---

## Building and Running Test Scripts

1. Navigate to the directory containing the cloned repository and run:

   ```bash
   docker compose build
   ```

2. **WIP:** Additional instructions will be added once the automated test scripts are implemented.

---

## Manual Testing

The following instructions explain how to start the Next.js website and interact with the containerized AI agent.

### Step 1: Start the Next.js Development Server

Open a terminal or command prompt and navigate to the Next.js project directory (the folder containing `package.json`).

Install the project dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The website should be accessible at:

**http://localhost:3000**

Keep this terminal running while testing.

### Step 2: Build the Docker Container

Open a **second terminal** and navigate to the repository directory containing `compose.yaml` or `docker-compose.yml`.

Build the Docker image:

```bash
docker compose build
```

### Step 3: Run the AI Agent

Ensure Ollama is running and the required model has been downloaded.

Start the AI agent:

```bash
docker compose run --rm opencode
```

You can now interact with the AI agent and provide instructions for manual testing.

### Step 4: Access the Container's Shell (Optional)

If you need to inspect files inside the running container, open another terminal.

List running containers:

```bash
docker ps
```

Find the container associated with the agent service. Copy its **CONTAINER ID** or **NAMES** value.

Access its shell:

```bash
docker exec -it <container_id> /bin/sh
```

Replace `<container_id>` with the actual container ID or name.

You can now inspect the container's filesystem using Linux commands.

To exit the container shell:

```bash
exit
```
