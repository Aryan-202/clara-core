# Installation Guide

This guide walks you through setting up `clara-core` locally for development and production deployment.

---

## 1. System Requirements

* **Python:** `3.11` or higher recommended (minimum `3.10+`)
* **Package Manager:** `pip` or `uv`
* **Operating System:** Linux, macOS, or Windows (WSL / PowerShell)

---

## 2. Clone the Repository

Clone the repository and enter the project root directory:

```bash
git clone https://github.com/Aryan-202/clara-core.git
cd clara-core
```

---

## 3. Create a Virtual Environment

It is strongly recommended to use a dedicated virtual environment:

### Linux / macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

---

## 4. Install Dependencies

Install the core dependencies along with documentation tools:

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Install editable package with docs extras
pip install -e .
```

---

## 5. Environment Configuration

Copy the example environment configuration to create your local `.env` file:

```bash
cp .env.example .env
```

### Required Configuration Keys

Edit `.env` and fill in the required API keys and OAuth parameters:

```ini
# --- OpenRouter / LLM Configuration ---
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-api-key
DEFAULT_MODEL=openai/gpt-4o-mini

# --- Google OAuth Credentials ---
GOOGLE_CLIENT_ID_WEB=your-google-web-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET_WEB=your-google-web-client-secret
GOOGLE_CLIENT_ID_DESKTOP=your-google-desktop-client-id.apps.googleusercontent.com

# --- Application Metadata ---
APP_NAME=Clara Core
APP_URL=https://github.com/Aryan-202/clara-core
PORT=8000
HOST=0.0.0.0
```

---

## 6. Verify Installation

Start the backend server to verify your installation:

```bash
clara
# or
python -m clara.main
```

Navigate to `http://localhost:8000/` in your browser. You should see:

```json
{
  "msg": "clara backend is running"
}
```
