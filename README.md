# Edukai AI Agent Service

This is an AI-powered recruitment automation engine built with **FastAPI** and **Docker**. It follows the **Cognitive-Deterministic Agentic Framework (CDAF)** to perform bulk CV qualification and individual CV and email Generation.

---

## 🚀 Features

* **Bulk Qualification:** Processes up to 500 CVs in parallel using OpenAI GPT-4o-mini.
* **Symbolic Scoring:** Deterministic logic to calculate experience and skill match without AI hallucination.
* **CV Regeneration:** Transforms raw data into standardized Edukai JSON format.
* **Email Specialist:** Generates professional pitch emails based on candidate profiles.
* **Dockerized Architecture:** Easy to deploy on any server.

---

## 🛠 Local Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd edukai-ai-agents
```

### 2. Configure Environment

Create a `.env` file in the root directory and add your keys (refer to the documentation).

### 3. Run with Docker

```bash
docker-compose up --build
```

---

## 🌐 Server Deployment Guide

Follow these steps to deploy this agent on a Linux Server.

---

### 1. Prerequisites

```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo systemctl enable docker
```

---

### 2. Clone & Prepare

```bash
git clone <your-repo-url>
cd edukai-ai-agents
```

---

### 3. Create .env on Server

```bash
nano .env
```

Add your production configuration:

```env
OPENAI_API_KEY=your_production_key
GET_CV_DATA_FOR_QUALIFICATION_API=your_internal_api_url
API_SECURITY_TOKEN=your_secure_token
```

---

### 4. Deploy in Detached Mode

Run the following command to start the service in the background:

```bash
docker-compose up --build -d
```

---

### 5. Managing the Service

```bash
# View Logs
docker-compose logs -f ai

# Stop Service
docker-compose down

# Restart Service
docker-compose restart ai
```

---

## 📦 Notes

* Ensure `.env` is never committed to version control.
* Use strong security tokens in production.
* Monitor logs regularly for performance and errors.
