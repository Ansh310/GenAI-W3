# Week 3 Submission – Research Desk

## Overview

For Week 3, I built **Research Desk**, a research-oriented AI agent that combines web search, academic paper search, persistent memory, and file-based note taking.

The goal was to move beyond a simple chatbot and create an agent capable of performing multi-step research tasks using tools.

---

## Features Implemented

### Persistent Sessions

Conversations are stored inside:

.agent/sessions/

Each session is saved as JSON and can be resumed later using the session ID.

This allows the agent to retain conversation history across runs.

---

### AGENTS.md Integration

The agent loads instructions from AGENTS.md at startup and includes them in the system prompt.

This provides procedural memory and allows project-specific behavior without modifying code.

---

### File Tools

Implemented:

* read_file
* write_file
* edit_file
* list_files

The tools are sandboxed to the workspace directory.

read_file supports line ranges and pagination.

edit_file supports:

* replace
* delete
* append

and returns a diff preview.

---

### Web Research Tools

Implemented:

* web_search
* web_fetch

web_search uses the Serper API to retrieve search results.

web_fetch downloads and extracts readable page content using trafilatura.

---

### Academic Paper Tools

Implemented:

* paper_search
* read_paper

paper_search queries the Hugging Face Papers API.

read_paper retrieves metadata and markdown content for a paper.

These tools allow the agent to use primary academic sources during research.

---

### Agent Architecture

The project follows a layered architecture:

Agent
├── REPLAgent
└── TUIAgent

The Agent class contains:

* conversation loop
* tool dispatch
* memory handling
* session management

UI-specific functionality is separated into REPLAgent and TUIAgent.

---

### User Interfaces

Implemented:

1. Interactive REPL

python agent.py

2. One-shot mode

python agent.py "What is Q-learning?"

3. Textual TUI

python agent.py --tui

---

## Challenges

The most challenging part was implementing the agent loop correctly using tool calling.

The model must:

1. Decide when to call a tool
2. Execute the tool
3. Process tool results
4. Continue reasoning
5. Produce a final response

Managing this iterative process while maintaining conversation state required careful message handling.

---

## What I Learned

Through this project I learned:

* OpenAI/OpenRouter tool calling
* Agent loops
* Persistent memory
* Procedural memory using AGENTS.md
* File-based knowledge storage
* Research workflows combining web and academic sources
* Separation of agent logic from UI logic

---

## Future Improvements

Potential future improvements include:

* Better session titles
* Session browser inside the TUI
* Citation tracking
* Automatic note generation
* Multi-agent research workflows
* RAG over saved notes

Overall, this project helped me understand how modern AI research assistants are structured and how tool-using agents are built.
