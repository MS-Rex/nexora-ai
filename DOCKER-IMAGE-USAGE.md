# Nexora AI - Docker Image Usage

A FastAPI-based AI microservice that can be easily deployed using Docker.

Run Nexora AI directly from the pre-built Docker image without cloning the repository.

## 🚀 Quick Start

### Prerequisites

- Docker installed on your system
- API keys for AI services (OpenAI, Anthropic, or Gemini)
- Logfire token

## 📥 Option 1: Load from File

If you have the `nexora-ai.tar.gz` file:

```bash
# Load the Docker image
docker load < nexora-ai.tar.gz
```

## 🚀 Run the Application

```bash
docker load < nexora-ai.tar.gz
docker run -d --name nexora-ai \
\-p 8000:8000 \
\--env-file .env \
nexora-ai
```

### Access the Application

- **API Base URL**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/api/v1/health`
- **Documentation**: `http://localhost:8000/docs`

### Test the Chat API

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer poc-key-123" \
  -d '{"message": "Hello", "session_id": "test_123"}'
```

### Stop the Application

```bash
docker stop nexora-ai
docker rm nexora-ai
```

## 🔑 Authentication

All API endpoints require Bearer token authentication: (added for testing purposes)

```bash
Authorization: Bearer poc-key-123
```

## 📋 Required Environment Variables

| Variable            | Required | Description                           |
| ------------------- | -------- | ------------------------------------- |
| `OPENAI_API_KEY`    | Yes\*    | Your OpenAI API key                   |
| `ANTHROPIC_API_KEY` | Yes\*    | Your Anthropic API key                |
| `GEMINI_API_KEY`    | Yes\*    | Your Google Gemini API key            |
| `LOGFIRE_TOKEN`     | Yes      | Your Logfire logging token            |
| `API_KEY`           | Yes      | Authentication key (use: poc-key-123) |

\*At least one AI API key is required for chat functionality.

## 📖 API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## 🐛 Troubleshooting

### Container won't start

```bash
# Check logs
docker logs nexora-ai

# Verify your environment variables
docker inspect nexora-ai
```

### Chat API returns "Connection refused"

- Ensure you have valid AI API keys in your environment variables
- Check that the container is running: `docker ps`
- Verify LOGFIRE_TOKEN is set

### Chat API returns errors

- Verify you have valid AI API keys
- Check that LOGFIRE_TOKEN is set
- Ensure you're using the Bearer token: `poc-key-123`

### Permission errors

- Ensure Docker daemon is running
- Try running with `sudo` (Linux) or restart Docker Desktop (macOS/Windows)
