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

Ollama is used to host the local language model.

Download and install [Ollama](https://ollama.com/download) for your operating system.

After installation, download the required model:

```bash
ollama pull qwen3:4b-instruct
```

Verify that the model is installed:

```bash
ollama list
```

Ensure Ollama is running before starting the AI agent.

**Important:** The Docker container must be able to connect to the Ollama server running on the host machine. The required network configuration may differ between Windows, macOS, and Linux.

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
docker compose run --rm agent
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
