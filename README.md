# MathTutor

**Math Tutor** is an intelligent, agentic AI assistant designed to help users solve math problems using a combination of document retrieval, web search, and reasoning via LLMs. The system is modular, agent-based, and built using modern protocols like **Model Context Protocol (MCP)** and **Agent to Agent (A2A) Protocol**, making it extensible and production-ready.

---

## Features

- **Retrieves relevant context** from a vector database (AstraDB)
- **Falls back to web search** if vector search yields no results
- **Uses LLMs for reasoning**, extracting and solving math questions
- **MCP-based microservices** for modularity and scalability
- **LangGraph orchestration** for flexible agent workflows
- **A2A-compatible responses** with structured artifacts
- **Automatic result saving** (raw + cleaned formats) for analysis
