
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

For consistent testing, the intended context window is **16,384 tokens**. Navigate to the Ollama app settings, find the context length slider and, increase to at least 16k.

If Ollama is managed by systemd on Linux, follow the Linux configuration below instead.

**Note:** OpenCode must also be configured with a compatible model context limit. Setting the Ollama environment variable alone does not guarantee that every request uses the specified context length. Increasing the context window also increases memory usage. The project is set up with a default configuration for a context length of 16k increasing it would require you to change the opencode.json file.

#### Configure Ollama Networking and Context (Linux Only)

On Linux, Ollama may listen only on `127.0.0.1`, preventing Docker containers from connecting.

The following configuration binds Ollama to the Docker bridge interface instead of all network interfaces. It also sets the default context window to 16,384 tokens.

This configuration assumes Ollama is installed as a systemd service and Docker's default bridge interface is available.

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

You should see Ollama listening on the configured Docker bridge address rather than `0.0.0.0`.

**5. Test Docker connectivity:**

From the directory containing `compose.yaml`:

```bash
docker compose run --rm --entrypoint /bin/sh opencode -c "curl -i http://host.docker.internal:11434/api/tags"
```

A successful connection should return an HTTP `200 OK` response.

When Ollama listens only on the Docker bridge IP, local Ollama CLI commands may also need to specify that address:

```bash
OLLAMA_HOST=172.17.0.1:11434 ollama list
```
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

## Building and Running the Test Harness

Before proceeding, ensure Docker, Python 3, Node.js, npm, and Ollama are installed and configured according to the dependencies section. Ensure Docker and Ollama are running and the required Qwen model is installed.

### 1. Build the Docker Image

Open a terminal, navigate to the root directory of the cloned repository (where `docker-compose.yml` is located), and run:

```bash
docker compose build
```

This builds the Docker image containing OpenCode and its required dependencies.

### 2. Start the Next.js Website

Open a second terminal and navigate to the `my-app` directory inside the cloned repository.

For the first launch only, install the required dependencies:

```bash
npm install
```

Then start the development server:

```bash
npm run dev
```

Keep this terminal running while executing the tests. The website should be accessible at `http://localhost:3000`.

### 3. Run the Test Harness

Oepn a second terminal and ensure you are in the repository directory containing `harness.py`.

**Windows:**

```bash
python harness.py
```

**macOS / Linux:**

```bash
python3 harness.py
```

**Note:** Depending on your Python installation, either `python` or `python3` may work on any operating system.

The test harness will initialize the Docker container, execute the prompt injection tests, report the results, and remove the testing container upon completion.
## Manual Testing (For developers Only)

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

**Note:** When accessing the Next.js development server from inside the Docker container, use `http://host.docker.internal:3000` instead of `http://localhost:3000`. The latter refers to the container itself.

On native Linux, the Next.js development server must also be reachable through the Docker host gateway. This may require adjusting the development server's listening address and verifying firewall rules.

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

---

## Troubleshooting

### Ollama Connection Errors

If OpenCode reports that it cannot connect to Ollama:

1. Verify that Ollama is running.
2. Confirm that `qwen3:4b-instruct` is installed.
3. Check that Ollama is listening on the expected address and port.
4. Verify that the container can reach the Ollama API using `host.docker.internal:11434`.
5. On Linux, verify the Docker host gateway mapping and any applicable firewall rules.

A successful API connection does not necessarily guarantee that model inference will complete successfully.

### Slow Responses or Timeouts

Local model inference performance depends on available hardware resources.

Systems with limited CPU, RAM, or GPU resources may experience slow responses or request timeouts, especially when running inside a virtual machine.

If requests time out while waiting for response headers, test Ollama inference directly before assuming the issue is related to Docker networking.
