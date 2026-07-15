# Deployment Specification

This document defines target environments, container structures, and verification checks.

---

## 1. Container Setup

We deploy Apex Credit using Docker Compose to orchestrate services:
- **Backend Service**: python:3.11-slim, runs the FastAPI ASGI server behind Uvicorn.
- **Frontend Service**: nginx:alpine, hosts static React SPA compilation files.
- **Database**: Standard SQLite engine volume mounted to ensure persistence.

---

## 2. Production Environment Checklist

1. **Secrets Security**: Use encrypted environment variables. Never commit `.env` containing production private values.
2. **CORS Headers**: Tighten CORS permissions in `main.py` to allow only specific subdomains.
3. **SSL Certificates**: Enforce HTTPS on the client reverse proxy.
4. **LLM Credentials**: Verify active OpenAI or Vertex API keys.

---

## 3. GitHub Actions Continuous Integration

The CI pipeline:
1. Triggers on pull requests and pushes to main.
2. Checks dependencies compilation.
3. Performs code formatting linting.
4. Builds Docker containers ensuring no static compilation failures.
