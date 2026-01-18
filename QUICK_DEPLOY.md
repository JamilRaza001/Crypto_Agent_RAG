# ⚡ Quick Deploy to Streamlit Cloud

## 5-Minute Deployment Guide

### Step 1: Commit & Push to GitHub (2 minutes)

```bash
# Check what changed
git status

# Add all deployment-ready files
git add .

# Commit with deployment message
git commit -m "Ready for Streamlit Cloud deployment - auto KB init added"

# Push to GitHub
git push origin main
```

### Step 2: Deploy on Streamlit Cloud (2 minutes)

1. **Go to**: [share.streamlit.io](https://share.streamlit.io)

2. **Sign in** with GitHub

3. **Click "New app"**

4. **Fill the form**:
   - Repository: `JamilRaza001/Crypto_Agent_RAG`
   - Branch: `main`
   - Main file: `streamlit_app/app.py`
   - App URL: `crypto-knowledge-agent` (or your choice)

5. **Click "Advanced settings"** → **"Secrets"**

6. **Paste this** (replace API key):
   ```toml
   GEMINI_API_KEY = "AIzaSyCG4puqoPQAZ-vbrkc9b8b26vTU1uW2a9k"
   CHROMA_DB_PATH = "./data/chromadb"
   SQLITE_DB_PATH = "./data/sqlite/metadata.db"
   EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
   GEMINI_MODEL = "gemini-2.5-flash"
   TEMPERATURE = "0.1"
   MAX_TOKENS = "2048"
   SIMILARITY_THRESHOLD = "0.5"
   TOP_K_RESULTS = "5"
   CHUNK_SIZE = "1000"
   CHUNK_OVERLAP = "200"
   PRICE_CACHE_TTL = "60"
   HISTORICAL_CACHE_TTL = "3600"
   TECHNICAL_CACHE_TTL = "300"
   FREECRYPTO_MONTHLY_LIMIT = "100000"
   GEMINI_RPM_LIMIT = "60"
   LOG_LEVEL = "INFO"
   ```

7. **Click "Deploy!"**

### Step 3: Wait & Test (1 minute)

1. Wait 2-3 minutes for:
   - Dependencies to install
   - Knowledge base to auto-initialize
   - App to start

2. **First-time setup shows**:
   - "🔄 First-time setup: Initializing knowledge base..."
   - "This may take 2-3 minutes. Please wait..."
   - "✅ Knowledge base initialized successfully!"

3. **Test the app**:
   - Ask: "What is Bitcoin?"
   - Check sidebar shows: "45+ crypto knowledge docs"
   - Ask: "What is the current BTC price?"

### Done! 🎉

Your app is live at:
```
https://crypto-knowledge-agent.streamlit.app
```

---

## Troubleshooting

**If deployment fails**, check logs in Streamlit Cloud dashboard.

**Common issues**:
- API key incorrect → Update in Secrets
- Module not found → Check requirements.txt
- KB initialization fails → Check logs, may need manual init

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed troubleshooting.

---

## Update Deployed App

```bash
# Make changes
git add .
git commit -m "Update XYZ"
git push origin main
```

Streamlit auto-deploys in 1-2 minutes!
