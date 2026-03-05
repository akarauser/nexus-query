# nexus-query
Agentic RAG System

Nexus Query is RAG system where you can use it to get insight of your PDF files while chatting with your model. You can do it privately, without internet connection on your local system. System saves the created documents for future conversations. Also it can remember single sessions history to keep conversation over the topic. By using agentic structure, it will answer your questions more accurately.

## Overview
- API Server: System let's you to call API from other interfaces
- Persistant Vector Store: System saves the created documents from your PDF file for you to use in future without recreating them
- Reranking: System rerank retrieved documents based on your prompt for better response
- Retriever Agent: System retrieves documents with agentic system to improve quality
- Short term Memory: System remembers single session conversations
- Guardrails: System tries to prevents prompt injection methods
- Tracing: System uses Langfuse to track input and output for you to evaluate your system usage

## Installation
* Application needs Docker. You can follow the steps from [Get Docker.](https://docs.docker.com/get-started/introduction/get-docker-desktop/)

* Install Langufe and get API keys. You can follow the steps from [Get Langfuse.](https://langfuse.com/self-hosting)

* Install application
```
git clone https://github.com/akarauser/nexus-query.git
cd nexus-query

copy .env.example .env (Edit credentials)

docker compose --env-file /path/to/.env up
```

## Usage
* Pull Ollama models (Only for first time):
> docker exec -it ollama_adaptor ollama pull nomic-embed-text:v1.5

*Make sure you have pulled **nomic-embed-text:v1.5** model for embeddings and choose another model with tool capability for application.*

* Go to http://localhost:8501/

##  License
MIT License (see LICENSE)

## Project Structure
```
nexus-query
├── .dockerignore
├── .env.example
├── .gitignore
├── .python-version
├── docker-compose.yml
├── Dockerfile
├── nexus_query
│   ├── .streamlit
│   │   └── config.toml
│   ├── app.py
│   ├── scripts
│   │   ├── api_server.py
│   │   ├── rag_system.py
│   │   ├── utils.py
│   │   └── __init__.py
│   └── __init__.py
├── pyproject.toml
├── README.md
├── tests
│   ├── test_system_main.py
│   └── __init__.py
└── uv.lock
```