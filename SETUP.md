# MediBot Setup Guide

Complete step-by-step guide to set up and run MediBot locally.

---

## ✅ Prerequisites Checklist

- [ ] Python 3.10 or later
- [ ] Node.js 18+ and npm/yarn
- [ ] Git
- [ ] GROQ API Key (get free at https://console.groq.com)
- [ ] (Optional) Docker for Qdrant persistence

---

## 🚀 Setup Steps

### Step 1: Prepare Data

The `mediassist_data/` folder should contain:
```
mediassist_data/
├── billing/
├── clinical/
├── equipment/
├── general/
├── nursing/
└── db/
    └── mediassist.db
```

If not yet downloaded, clone from:
```
https://github.com/MouneshV/MediBot_Project/tree/ce2c9e1a2b9790cdf40dcf3dcf73c4678181aedf/mediassist_data
```

### Step 2: Backend Setup

#### 2.1 Create Virtual Environment

```bash
cd backend
python -m venv venv
```

Activate:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

#### 2.2 Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn
- Docling (PDF parsing)
- Qdrant client
- Sentence-Transformers (embeddings)
- Groq client
- And more...

**Note:** First install may take 5–10 minutes (Docling has heavy dependencies).

#### 2.3 Configure Environment

```bash
# Copy template
cp .env.sample .env

# Edit .env and set your GROQ API key
# GROQ_API_KEY=gsk_your_key_here
```

#### 2.4 (Optional) Start Qdrant

If you want persistent vector storage:

```bash
# Make sure Docker is running
docker run -d -p 6333:6333 qdrant/qdrant
```

If Docker is unavailable, the app will use in-memory Qdrant (fine for testing).

#### 2.5 Ingest Documents

```bash
# Still in backend/ directory, with venv active
python ingestion/ingest.py
```

This will:
- Parse all PDFs & Markdown files
- Generate embeddings (dense + BM25)
- Upload to Qdrant with RBAC metadata
- **Expected time:** 5–15 minutes

**Output:** You should see log messages like:
```
[INFO] Chunked document.pdf into 25 chunks (Docling)
[INFO] Generating dense embeddings...
[INFO] Uploading to Qdrant...
[INFO] Ingestion complete! 250 chunks stored in 'medibot_docs'
```

#### 2.6 Start Backend Server

```bash
python main.py
```

**Output:**
```
[INFO] MediBot Backend Starting...
[INFO] Uvicorn running on http://0.0.0.0:8000
```

✅ Backend is ready. Leave this terminal running.

---

### Step 3: Frontend Setup

#### 3.1 Navigate to Frontend

```bash
cd frontend  # or cd ../frontend from backend/
```

#### 3.2 Install Dependencies

```bash
npm install
```

#### 3.3 Configure Environment

```bash
cp .env.sample .env.local

# Verify NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### 3.4 Start Frontend Dev Server

```bash
npm run dev
```

**Output:**
```
- ready started server on 0.0.0.0:3000, url: http://localhost:3000
```

✅ Frontend is ready.

---

## 🌐 Access the Application

1. **Open browser:** http://localhost:3000
2. **Login** with any demo account:
   - Username: `dr.mehta` | Password: `doctor123` (or use quick-login buttons)
3. **Ask questions:**
   - "What's the treatment for acute myocardial infarction?" (doctors only)
   - "What are ICU nursing procedures?" (nurses)
   - "Show me all billing codes" (billing executives)
   - "How many maintenance tickets are open?" (admin analytics)

---

## 🧪 Testing RBAC

### Test 1: Doctor Access to Clinical Documents ✅

1. Login as `dr.mehta` (doctor)
2. Ask: "What clinical protocols are available?"
3. ✅ Should receive clinical documents

### Test 2: Nurse Cannot Access Billing ❌

1. Login as `nurse.priya` (nurse)
2. Ask: "Show me all insurance billing codes"
3. ❌ Should receive message: "As a nurse, you don't have access to billing documents..."

### Test 3: Admin Can Access All

1. Login as `admin.sys` (admin)
2. Ask any question from any collection
3. ✅ Should receive answer from all collections

---

## 🛠️ Troubleshooting

### Backend Won't Start

**Error:** `ModuleNotFoundError: No module named 'docling'`

**Solution:**
```bash
pip install docling docling-core --upgrade
```

**Error:** `Connection to Qdrant failed`

**Solution:**
- Option 1: Start Docker Qdrant
- Option 2: Leave as-is (in-memory mode will activate automatically)

### Frontend Shows "Error Sending Message"

**Check:**
1. Backend running? (`python main.py` in backend terminal)
2. `NEXT_PUBLIC_API_URL` correct in `frontend/.env.local`
3. Browser console (F12) for network errors
4. Restart frontend: `npm run dev`

### Ingestion Failed

**Check:**
- All data files in `mediassist_data/` are readable?
- Enough disk space for embeddings?
- GROQ_API_KEY set (not needed for ingestion, but good to verify)?

---

## 📊 System Architecture Overview

```
┌──────────────────────┐
│   Next.js Frontend   │  (Port 3000)
│  (Chat Interface)    │
└──────────┬───────────┘
           │ HTTP + JWT
           ▼
┌──────────────────────────────┐
│   FastAPI Backend            │  (Port 8000)
│  - Routers                   │
│  - Auth                      │
│  - RAG Pipeline              │
└──┬─────────────────────────┬─┘
   │                         │
   ▼                         ▼
┌─────────────────┐  ┌──────────────────┐
│ Qdrant Vector   │  │  Groq LLM        │
│ Store + BM25    │  │  + Cross-encoder │
│ + RBAC Filter   │  │                  │
└─────────────────┘  └──────────────────┘
```

---

## 📈 Performance Tips

### Faster Ingestion
- Use GPU if available (Docling will auto-detect)
- Increase batch size in `ingest.py` if RAM permits

### Faster Queries
- Ensure Qdrant is running (not in-memory mode)
- Use GROQ (already fast) or cache embeddings

### Production Deployment
- Use persistent Qdrant (Docker volume or cloud)
- Deploy FastAPI with `gunicorn` or `uvicorn` + reverse proxy
- Deploy frontend with `npm run build && npm start`

---

## ✅ Verification Checklist

- [ ] Backend started without errors (`python main.py`)
- [ ] Frontend accessible (`http://localhost:3000`)
- [ ] Can login with `dr.mehta` / `doctor123`
- [ ] Can send chat message and get response
- [ ] Response includes source citations
- [ ] Role badge shows user's role and accessible collections
- [ ] RBAC works: nurse cannot access billing docs

---

## 📚 Next Steps

1. **Customize demo accounts** in `backend/config.py` (USERS dict)
2. **Add new collections** in `mediassist_data/` and re-run ingestion
3. **Fine-tune prompts** in `backend/retrieval/rag_chain.py`
4. **Deploy** to production environment

---

## 📖 Documentation

- **Full README:** See `README.md`
- **Implementation Plan:** See `implementation_plan.md`
- **API Docs:** Visit `http://localhost:8000/docs` (Swagger UI)

---

## 💬 Support

For issues:
1. Check **Troubleshooting** section above
2. Review logs in terminal windows
3. Verify all environment variables are set
4. Ensure all data files exist

---

**Happy chatting with MediBot! 🏥**
