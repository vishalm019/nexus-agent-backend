# Nexus Agent: Agentic RAG Backend

A high-performance, secure Python backend for an Agentic AI Assistant.

## Core Features
- **Autonomous Tool Calling**  
  Uses a custom-built loop to allow the LLM to create, update, and delete tasks in a PostgreSQL database via structured JSON commands.

- **RAG (Retrieval-Augmented Generation)**  
  Implements semantic search using pgvector and Hugging Face embeddings to ground the AI in personal knowledge.

- **Secure Multi-Tenancy**  
  State-of-the-art authentication using JWT (JSON Web Tokens) and salted password hashing.

- **Dockerized Infrastructure**  
  Fully containerized setup with a dedicated Vector DB and Flask application for seamless deployment.

## Tech Stack
- **Brain:** Llama-3 (via Groq) / GPT-OSS
- **Database:** PostgreSQL with pgvector
- **Framework:** Flask
- **Authentication:** Flask-JWT-Extended
- **DevOps:** Docker, Docker-Compose, WSL 2

## Quick Start (Docker)
1. Clone the repo and add your `.env` file  
2. Run:
   ```bash
   docker-compose up --build
