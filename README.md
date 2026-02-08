# 🛡️ Nexus Agent: Agentic RAG Backend

A **high-performance, secure Python backend** for an Agentic AI Assistant.  
This system doesn’t just *chat* — it manages tasks, maintains long-term memory, and makes autonomous decisions using **structured Tool Calling**.

---

## 🚀 Core Features

- **Autonomous Tool Calling**
  - Uses a custom reasoning loop that allows the LLM to **Create, Update, and Delete tasks** in a PostgreSQL database via structured JSON commands.

- **RAG (Retrieval-Augmented Generation)**
  - Implements semantic search using **pgvector** and **Hugging Face embeddings** to ground the AI in personal knowledge and project metrics.

- **Secure Multi-Tenancy**
  - Authentication using **JWT (JSON Web Tokens)** and **salted password hashing** for strict data isolation.

- **Dockerized Infrastructure**
  - Fully containerized setup with a dedicated **Vector DB** and **Flask application** for seamless, cross-platform deployment.

---

## 🛠️ Tech Stack

- **Brain:** Llama-3 (via Groq) / GPT-OSS  
- **Database:** PostgreSQL with `pgvector` extension  
- **Framework:** Flask  
- **Authentication:** Flask-JWT-Extended  
- **DevOps:** Docker, Docker Compose, WSL 2  

---

## 🔍 Technical Deep Dive

### 1️⃣ Agentic Architecture & MCP Logic

Unlike traditional chatbots, **Nexus Agent** implements a **Single-Agent Tool-Using Pattern**.

- **Cognitive Loop**
  - The agent analyzes user intent to decide between a direct response or a database operation.

- **Structured Tool Calling**
  - Instead of parsing raw text, the agent generates **structured JSON payloads** based on a defined function schema.
  - This follows **Model Context Protocol (MCP)** principles, making the tool interface modular and scalable.

- **Autonomous CRUD**
  - The agent independently manages the task lifecycle.
  - Example:  
    > *“I’ve finished that IITM report”*  
    → `update_task(status="Completed")`

---

### 2️⃣ Semantic Memory (RAG)

To provide **context-aware assistance**, the system uses a Retrieval-Augmented Generation pipeline.

- **Vector Embeddings**
  - Technical specifications and project data are converted into **768-dimensional vectors** using the `all-mpnet-base-v2` model.

- **Similarity Search**
  - Uses **pgvector** with the `<=>` (cosine distance) operator to retrieve the **top-k relevant memories** per query.

- **Database Grounding**
  - Retrieved context is injected into the system prompt, significantly reducing hallucinations and improving factual accuracy.

---

### 3️⃣ Production-Ready Infrastructure

- **Containerization**
  - Flask app, PostgreSQL, and pgvector are orchestrated using **Docker Compose**.
  - Ensures identical environments across **WSL 2, Linux, and Production servers**.

- **Security & Isolation**
  - Every agent action is bound to a `user_id` derived from the JWT identity.
  - Guarantees a **secure multi-tenant architecture** where users only access their own data.

---

## ⚡ Quick Start (Docker)

1. Clone the repository  
2. Create a `.env` file and add:
   - Groq API key
   - Hugging Face API key

3. Launch the stack:
   ```bash
   docker-compose up --build

4. Access the API: 
    ```bash
    http://localhost:3400