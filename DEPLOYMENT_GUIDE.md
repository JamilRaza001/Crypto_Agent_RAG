# 🚀 Streamlit Cloud Deployment Guide

Complete guide to deploy your Crypto Knowledge Agent on Streamlit Cloud.

---

## Prerequisites

1. ✅ GitHub account
2. ✅ Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
3. ✅ Google Gemini API key ([Get it here](https://makersuite.google.com/app/apikey))
4. ✅ Your code pushed to GitHub repository

---

## Step 1: Prepare Your Repository

### 1.1 Commit All Changes

```bash
# Check current status
git status

# Add all files (knowledge base, config, etc.)
git add .

# Commit changes
git commit -m "Prepare for Streamlit Cloud deployment"

# Push to GitHub
git push origin main
```

### 1.2 Verify Files Are in GitHub

Make sure these files are pushed:
- ✅ `streamlit_app/app.py` (main entry point)
- ✅ `requirements.txt` (dependencies)
- ✅ `.streamlit/config.toml` (Streamlit config)
- ✅ `.streamlit/secrets.toml.example` (template)
- ✅ `data/knowledge_base/raw/` (your 45+ documents)
- ✅ All `src/` files (core application)
- ✅ All `config/` files

**DO NOT push:**
- ❌ `.env` (contains API keys)
- ❌ `.streamlit/secrets.toml` (if exists)
- ❌ `data/chromadb/*` (will be regenerated)
- ❌ `data/sqlite/*.db` (will be regenerated)

---

## Step 2: Sign Up for Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "Sign up with GitHub"
3. Authorize Streamlit to access your repositories
4. Select your repository: `JamilRaza001/Crypto_Agent_RAG`

---

## Step 3: Deploy Your App

### 3.1 Create New App

1. Click **"New app"** button
2. Fill in the form:
   - **Repository**: `JamilRaza001/Crypto_Agent_RAG`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app/app.py`
   - **App URL**: Choose a custom URL (e.g., `crypto-knowledge-agent`)

### 3.2 Configure Secrets

Before deploying, click **"Advanced settings"** → **"Secrets"**

Copy and paste this (replace with your actual API key):

```toml
# Google Gemini API
GEMINI_API_KEY = "AIzaSyCG4puqoPQAZ-vbrkc9b8b26vTU1uW2a9k"

# ChromaDB Settings (relative paths for cloud)
CHROMA_DB_PATH = "./data/chromadb"
SQLITE_DB_PATH = "./data/sqlite/metadata.db"

# Model Settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GEMINI_MODEL = "gemini-2.5-flash"
TEMPERATURE = "0.1"
MAX_TOKENS = "2048"

# RAG Settings
SIMILARITY_THRESHOLD = "0.5"
TOP_K_RESULTS = "5"
CHUNK_SIZE = "1000"
CHUNK_OVERLAP = "200"

# Cache Settings
PRICE_CACHE_TTL = "60"
HISTORICAL_CACHE_TTL = "3600"
TECHNICAL_CACHE_TTL = "300"

# Rate Limiting
FREECRYPTO_MONTHLY_LIMIT = "100000"
GEMINI_RPM_LIMIT = "60"

# Logging
LOG_LEVEL = "INFO"
```

### 3.3 Deploy

1. Click **"Deploy!"**
2. Wait 2-5 minutes for deployment
3. Watch the logs in the Streamlit Cloud dashboard

---

## Step 4: Initialize Knowledge Base (First Deployment)

**IMPORTANT**: On first deployment, the knowledge base needs to be initialized.

### Option A: Add Initialization to App Startup

The app will auto-initialize on first run if ChromaDB is empty.

### Option B: Manual Initialization (if needed)

If the app fails on first run:

1. Add this to `streamlit_app/app.py` at the top of `main()`:

```python
def main():
    """Main application."""

    # Initialize KB on first run
    import os
    if not os.path.exists('data/chromadb/chroma.sqlite3'):
        with st.spinner("Initializing knowledge base (first run)..."):
            from scripts.init_kb import main as init_kb
            init_kb()

    initialize_session_state()
    # ... rest of code
```

2. Commit and push:

```bash
git add streamlit_app/app.py
git commit -m "Add auto KB initialization for cloud deployment"
git push origin main
```

3. Streamlit will auto-redeploy

---

## Step 5: Update Settings for Cloud

### 5.1 Update `config/settings.py` to Read from Streamlit Secrets

The app already uses `os.getenv()` which works with Streamlit secrets automatically!

Streamlit secrets are available as:
- `st.secrets["GEMINI_API_KEY"]`
- OR as environment variables (current implementation)

**No code changes needed!** ✅

---

## Step 6: Verify Deployment

### 6.1 Check App Status

1. Go to your Streamlit Cloud dashboard
2. Check the app status (should be green)
3. Click the app URL to open it

### 6.2 Test the App

1. **Check Knowledge Base**: Sidebar should show "45+ crypto knowledge docs"
2. **Test Query**: Ask "What is Bitcoin?"
3. **Check Sources**: Should show retrieved documents
4. **Check API**: Ask "What is the current BTC price?"

### 6.3 Monitor Logs

In Streamlit Cloud dashboard:
- Click **"Manage app"** → **"Logs"**
- Watch for any errors
- Check initialization messages

---

## Troubleshooting

### Issue 1: "Module not found" Error

**Solution**: Check `requirements.txt` includes all dependencies

```bash
# Locally test requirements
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

### Issue 2: "Knowledge Base Empty" Error

**Solution**:
1. Verify `data/knowledge_base/raw/` files are in GitHub
2. Add auto-initialization (see Step 4, Option B)
3. Check logs for ChromaDB errors

### Issue 3: "API Key Invalid" Error

**Solution**:
1. Go to Streamlit Cloud → App Settings → Secrets
2. Verify `GEMINI_API_KEY` is correct
3. No quotes around the key in secrets.toml
4. Save and reboot app

### Issue 4: App Crashes on Startup

**Solution**:
1. Check logs in Streamlit Cloud
2. Verify all paths use relative paths (not Windows paths)
3. Ensure ChromaDB directory exists:

```bash
# In repository
mkdir -p data/chromadb
mkdir -p data/sqlite
touch data/chromadb/.gitkeep
touch data/sqlite/.gitkeep
git add data/
git commit -m "Add data directories"
git push
```

### Issue 5: Slow First Load

**Expected**: First deployment takes 2-5 minutes to:
- Install dependencies
- Download embedding models
- Initialize ChromaDB
- Index knowledge base

Subsequent loads are much faster!

---

## Configuration Tips

### 1. Custom Domain (Optional)

Streamlit Cloud allows custom domains:
1. Go to App Settings
2. Click "Domains"
3. Add your custom domain
4. Follow DNS instructions

### 2. Resource Limits

**Streamlit Free Tier**:
- 1 GB RAM
- Shared CPU
- Good for demo/testing

**Streamlit Teams** (if you upgrade):
- More resources
- Private apps
- Custom authentication

### 3. Embedding Model

For faster cloud deployment, consider using a smaller embedding model in `secrets.toml`:

```toml
# Faster alternative
EMBEDDING_MODEL = "sentence-transformers/paraphrase-MiniLM-L3-v2"
```

---

## Security Best Practices

1. ✅ **Never commit API keys** to GitHub
2. ✅ **Use Streamlit secrets** for all sensitive data
3. ✅ **Rotate API keys** periodically
4. ✅ **Monitor API usage** in Google Cloud Console
5. ✅ **Set rate limits** to prevent abuse

---

## Updating Your Deployed App

### Push Updates

```bash
# Make your changes
git add .
git commit -m "Update feature X"
git push origin main
```

Streamlit Cloud will **auto-deploy** within 1-2 minutes!

### Update Secrets

1. Go to Streamlit Cloud → App Settings → Secrets
2. Edit secrets
3. Click "Save"
4. App will auto-restart

---

## Cost Breakdown

### Free Resources:
- ✅ Streamlit Cloud (free tier)
- ✅ FreeCryptoAPI (100K requests/month)
- ✅ GitHub (public repo)

### Paid Resources:
- 💰 Google Gemini API (~$0.0001 per request)
  - Free tier: 15 requests/minute
  - Paid tier: As needed

**Estimated cost**: ~$0-5/month for moderate usage

---

## Your Deployed App URL

After deployment, your app will be available at:

```
https://crypto-knowledge-agent.streamlit.app
```

(Or your custom URL)

---

## Quick Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] `.streamlit/config.toml` committed
- [ ] `requirements.txt` up to date
- [ ] Knowledge base files in `data/knowledge_base/raw/`
- [ ] Signed up for Streamlit Cloud
- [ ] Connected GitHub repository
- [ ] Added secrets in Streamlit Cloud
- [ ] Deployed app
- [ ] Tested basic functionality
- [ ] Verified knowledge base works
- [ ] Tested API calls

---

## Support & Resources

- **Streamlit Docs**: https://docs.streamlit.io/streamlit-community-cloud
- **Gemini API**: https://ai.google.dev/
- **Your GitHub Repo**: https://github.com/JamilRaza001/Crypto_Agent_RAG

---

## 🎉 Congratulations!

Your Crypto Knowledge Agent is now live on the internet!

Share the URL with others and showcase your AI-powered crypto assistant! 🚀
