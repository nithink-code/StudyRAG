# Deployment Guide: StudyRAG Project

This guide provides step-by-step instructions to deploy your **FastAPI Backend on Vercel** and your **Streamlit Frontend on Streamlit Cloud**.

Since this project has two distinct parts (an API backend and a Streamlit UI), we deploy them separately to their best-suited platforms.

---

## 1. Prerequisites

Before you begin, ensure you have:
- A [GitHub](https://github.com/) account with this code pushed to a repository.
- A [Vercel](https://vercel.com/) account (for the Backend).
- A [Streamlit Community Cloud](https://streamlit.io/cloud) account (for the Frontend).
- An [Inngest Cloud](https://innngest.com/) account.
- A [Qdrant Cloud](https://qdrant.tech/) account (Managed Cluster).
- An [OpenRouter](https://openrouter.ai/) API Key.

---

## 2. Obtaining Required API Keys/Secrets

You need to gather these 5 values before deploying.

### A. Inngest Cloud (Orchestration)
1.  **Sign Up/Login**: Go to [app.inngest.com](https://app.inngest.com/).
2.  **Create App**: If prompted, create a new workspace/app.
3.  **Get Event Key**:
    -   Go to **"Manage"** -> **"Event Keys"**.
    -   Copy the "Default Key". This is your `INNGEST_EVENT_KEY`.
4.  **Get Signing Key**:
    -   Go to **"Manage"** -> **"Signing Key"**.
    -   Click to reveal and copy the key. This is your `INNGEST_SIGNING_KEY`.

### B. Qdrant Cloud (Vector Database)
1.  **Sign Up/Login**: Go to [cloud.qdrant.io](https://cloud.qdrant.io/).
2.  **Create Cluster**: Click **"Create Cluster"**. Select the **Free Tier**.
3.  **Get API Key**:
    -   Once the cluster is running, click **"Data Access Control"** (or "API Keys") on the left menu.
    -   Create a new key and copy it. This is your `QDRANT_API_KEY`.
4.  **Get Cluster URL**:
    -   Go to **"Cluster Dashboard"**.
    -   Copy the **Endpoint URL** (e.g., `https://xyz-example.us-east4-0.gcp.cloud.qdrant.io`). This is your `QDRANT_URL`.

### C. OpenRouter (AI Model Access)
1.  **Sign Up/Login**: Go to [openrouter.ai](https://openrouter.ai/).
2.  **Create Key**:
    -   Go to [openrouter.ai/keys](https://openrouter.ai/keys).
    -   Click **"Create Key"**.
    -   Name it (e.g., "StudyRAG") and copy the string starting with `sk-or-...`. This is your `OPENROUTER_API_KEY`.

---

## 3. Prepare the Code

### A. Add Vercel Configuration
A `vercel.json` file has been added to your `StudyRAG/` folder. This tells Vercel how to build your Python app.

### B. Code Updates (Already Completed)
The code has already been updated to support production environments:
-   `streamlit_app.py` handles text extraction locally and uses authenticated Inngest calls.
-   `vector_db.py` uses environment variables for cloud connection.
-   `main.py` accepts text payloads instead of requiring local file paths.

---

## 4. Deploy Backend to Vercel

1.  **Log in to Vercel** and click "Add New..." > "Project".
2.  **Import your GitHub Repository**.
3.  **Configure Project**:
    -   **Root Directory**: Click "Edit" and select `StudyRAG`.
    -   **Framework Preset**: Select "Other" (or leave as handled by `vercel.json`).
    -   **Environment Variables**: expand the section and add the keys you gathered in Step 2:
        -   `INNGEST_SIGNING_KEY`
        -   `INNGEST_EVENT_KEY`
        -   `OPENROUTER_API_KEY`
        -   `QDRANT_API_KEY`
        -   `QDRANT_URL`
4.  **Click Deploy**.
5.  Once deployed, copy your **Domains** URL (e.g., `https://your-project.vercel.app`).

### Connect Vercel to Inngest Cloud
1.  Go to your [Inngest Cloud Dashboard](https://app.inngest.com/).
2.  Go to **Apps** and look for your app.
3.  If it's not automatically detected, verify your Vercel deployment is live by visiting `https://your-project.vercel.app/api/inngest` in a browser. It should say "Inngest API is running".
4.  Inngest Cloud will automatically sync with your Vercel app.

---

## 5. Deploy Frontend to Streamlit Cloud

1.  **Log in to Streamlit Community Cloud**.
2.  Click "New app".
3.  **Select Repository**: Choose your repo.
4.  **Main file path**: Enter `StudyRAG/streamlit_app.py`.
5.  **Advanced settings** -> **Secrets** (Environment Variables):
    Add the required secrets in TOML format:
    ```toml
    INNGEST_EVENT_KEY = "your_inngest_event_key"
    INNGEST_SIGNING_KEY = "your_inngest_signing_key"
    INNGEST_API_BASE = "https://api.inngest.com/v1"
    ```
6.  **Click Deploy**.

---

## 6. Usage

1.  Open your deployed Streamlit App.
2.  Upload a PDF.
3.  Ask a question.
4.  The app will send the event to Inngest Cloud, which triggers your Vercel Backend to process the file and generate an answer.
