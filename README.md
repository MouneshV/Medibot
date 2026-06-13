# 🏥 MediBot — Intelligent Medical Assistant with RBAC & RAG

An advanced **Retrieval-Augmented Generation (RAG)** system for MediAssist Health Network with **Role-Based Access Control (RBAC)**, hybrid search capabilities, and intelligent routing to specialized RAG chains.

## 🎯 Overview

MediBot is a full-stack AI-powered medical assistant that:
- 🔐 **Enforces RBAC** — Different staff roles access different documents
- 🔍 **Hybrid Search** — Combines dense + BM25 sparse retrieval with Reciprocal Rank Fusion
- 🏆 **Reranking** — Cross-encoder reranking to surface the most relevant documents
- 🤖 **LLM Integration** — Uses Groq's API for fast, cost-effective inference
- 📊 **SQL RAG** — Routes analytical questions to NL→SQL→Execute pipeline
- 🚀 **Production-Ready** — Deployed with Next.js frontend and FastAPI backend

---

## ✨ Key Features

### Backend Features
- **Multi-Document RAG** — Supports PDFs and Markdown with hierarchical chunking
- **Hybrid Retrieval** — Dense embeddings (Sentence-Transformers) + BM25 sparse search
- **RBAC Security** — Metadata-based filtering at Qdrant query level (not post-retrieval)
- **Smart Routing** — Routes to SQL RAG for analytical questions, Hybrid RAG for general queries
- **JWT Authentication** — Secure token-based API access
- **CORS Enabled** — Development-friendly cross-origin configuration

### Frontend Features
- **Modern UI** — Built with Next.js 15 and React 19
- **Real-Time Chat** — Streaming message interface with typing indicators
- **Source Citation** — Shows retrieved documents and sections with metadata
- **Role-Based Views** — Different users see different document collections
- **Demo Accounts** — Quick-login buttons for testing different roles

### Supported Medical Roles
- 👨‍⚕️ **Doctor** — Access to clinical, nursing, and general documents
- 👩‍⚕️ **Nurse** — Access to nursing and general documents
- 💼 **Billing Executive** — Access to billing and general documents
- 🔧 **Technician** — Access to equipment and general documents
- 🔐 **Admin** — Full access to all documents

---

## 📋 Prerequisites

- **Python** 3.10 or later
- **Node.js** 18+ with npm
- **GROQ API Key** (free at https://console.groq.com)
- **Git** (for cloning)
- **Docker** (optional, for persistent Qdrant)

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Medibot
```

### 2. Prepare Environment

```bash
# Set up backend
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure .env
cp .env.sample .env
# Edit .env and add your GROQ_API_KEY
```

### 3. Ingest Documents

```bash
# Still in backend/ with venv activated
python ingestion/ingest_fallback_only.py
```

This creates a persistent Qdrant database at `./qdrant_storage` with 91 chunks from 12 medical documents.

### 4. Start Backend

```bash
# From backend/ directory
python main.py
```

Backend will start on `http://localhost:8000`

### 5. Start Frontend (New Terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend will start on `http://localhost:3000`

### 6. Access the Application

Open http://localhost:3000 in your browser and login with demo credentials:

| Role | Username | Password |
|------|----------|----------|
| 👨‍⚕️ Doctor | `dr.mehta` | `doctor123` |
| 👩‍⚕️ Nurse | `nurse.priya` | `nurse123` |
| 💼 Billing | `billing.ravi` | `billing123` |
| 🔧 Technician | `tech.anand` | `tech123` |
| 🔐 Admin | `admin.sys` | `admin123` |

---

## 📁 Project Structure

```
Medibot/
├── backend/                          # FastAPI server
│   ├── main.py                       # Application entry point
│   ├── config.py                     # Configuration & RBAC matrix
│   ├── auth.py                       # JWT authentication
│   ├── models.py                     # Pydantic schemas
│   ├── requirements.txt              # Python dependencies
│   ├── .env                          # Environment variables (API keys)
│   │
│   ├── ingestion/                    # Document ingestion pipeline
│   │   ├── ingest.py                 # Full ingestion orchestration
│   │   ├── ingest_fallback_only.py  # Ingestion without Docling
│   │   ├── parser.py                 # PDF/Markdown parsing
│   │   ├── chunker.py                # Hierarchical chunking
│   │   └── __init__.py
│   │
│   ├── retrieval/                    # RAG & retrieval modules
│   │   ├── hybrid_search.py          # Dense + BM25 hybrid search with RBAC
│   │   ├── reranker.py               # Cross-encoder reranking
│   │   ├── rag_chain.py              # Full RAG pipeline
│   │   ├── sql_chain.py              # SQL RAG for analytical queries
│   │   └── __init__.py
│   │
│   ├── routers/                      # API endpoints
│   │   ├── auth_router.py            # POST /login
│   │   ├── chat.py                   # POST /chat
│   │   ├── collections.py            # GET /collections/{role}
│   │   └── __init__.py
│   │
│   ├── sql_rag/                      # SQL RAG support
│   ├── source/                       # Virtual environment (venv)
│   └── qdrant_storage/               # Persistent Qdrant database
│
├── frontend/                         # Next.js application
│   ├── package.json                  # Node dependencies
│   ├── next.config.js                # Next.js configuration
│   ├── jsconfig.json                 # Path aliases for imports
│   │
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.js               # Login page
│   │   │   ├── layout.js             # Root layout
│   │   │   ├── globals.css           # Global styles
│   │   │   ├── login.css             # Login page styles
│   │   │   └── chat/
│   │   │       ├── page.js           # Chat interface page
│   │   │       └── chat.css          # Chat page styles
│   │   │
│   │   ├── components/               # React components
│   │   │   ├── LoginForm.jsx         # Login form
│   │   │   ├── ChatInterface.jsx     # Chat UI
│   │   │   ├── MessageBubble.jsx     # Message display
│   │   │   ├── SourceCitation.jsx    # Source display
│   │   │   ├── RoleBadge.jsx         # Role badge
│   │   │   └── *.css                 # Component styles
│   │   │
│   │   └── lib/
│   │       └── api.js                # API client (axios wrapper)
│   │
│   └── node_modules/                 # Node dependencies
│
├── mediassist_data/                  # Medical documents
│   ├── billing/                      # Billing documents
│   ├── clinical/                     # Clinical protocols
│   ├── equipment/                    # Equipment manuals
│   ├── general/                      # General documents
│   ├── nursing/                      # Nursing procedures
│   └── db/
│       └── mediassist.db             # SQLite database for SQL RAG
│
├── README.md                         # This file
├── BUILD_COMPLETE.md                 # What's been implemented
├── SETUP.md                          # Detailed setup guide
└── implementation_plan.md            # Project architecture
```

---

## 🔌 API Endpoints

All endpoints except `/login` require JWT authentication via `Authorization: Bearer <token>` header.

### Authentication
- **POST** `/login` — Login with username/password
  ```json
  {
    "username": "dr.mehta",
    "password": "doctor123"
  }
  ```
  Returns: JWT token, role, username, display name, accessible collections

### Chat & Retrieval
- **POST** `/chat` — Ask a medical question
  ```json
  {
    "question": "What are the treatment protocols for Type 2 Diabetes?"
  }
  ```
  Returns: Answer, source documents, retrieval type (hybrid_rag or sql_rag), user role

- **GET** `/collections/{role}` — List accessible document collections
  - Parameters: `role` (doctor, nurse, billing_executive, technician, admin)
  - Returns: List of collections accessible to the role

### Health & Docs
- **GET** `/health` — Health check endpoint
- **GET** `/docs` — Swagger UI for interactive API documentation

---

## 🔐 RBAC Implementation

Role-based access control is enforced at the **Qdrant query level**, not post-retrieval:

```python
# Every query is filtered by access_roles metadata
rbac_filter = Filter(
    must=[
        FieldCondition(
            key="access_roles",
            match=MatchAny(any=[user_role]),
        )
    ]
)
```

This ensures:
- ✅ Adversarial prompts cannot bypass RBAC
- ✅ Only authorized documents are retrieved
- ✅ No filtering needed after retrieval

---

## 🔄 RAG Pipeline

### For General Questions:
```
User Question
    ↓
Hybrid Search (Dense + BM25)
    ↓
RBAC Filtering at Qdrant level
    ↓
Top-10 Candidates Retrieved
    ↓
Cross-Encoder Reranking
    ↓
Top-3 Chunks Selected
    ↓
Groq LLM Generation
    ↓
Answer with Source Citations
```

### For Analytical Questions:
```
User Question (contains keywords like "how many", "count", "total", etc.)
    ↓
SQL RAG Route (if user role permits)
    ↓
NL → SQL Generation
    ↓
Execute on mediassist.db
    ↓
Format Results as Natural Language
    ↓
Return Answer
```

---

## 🛠 Troubleshooting

### "Network Error" on Chat
**Problem:** Frontend cannot connect to backend
- **Solution:** Ensure backend is running on `http://localhost:8000`
- **Check:** Open http://localhost:8000/health in your browser

### "Collection medibot_docs not found"
**Problem:** No data in Qdrant
- **Solution:** Run ingestion script again
  ```bash
  cd backend
  python ingestion/ingest_fallback_only.py
  ```

### "Login Failed. Please try again."
**Problem:** Backend not responding or wrong credentials
- **Solution:**
  1. Check backend is running: `http://localhost:8000/docs`
  2. Verify credentials from the demo accounts table above
  3. Ensure JWT_SECRET matches in `.env`

### Import errors on backend startup
**Problem:** Missing Python dependencies
- **Solution:**
  ```bash
  cd backend
  source venv/bin/activate  # or venv\Scripts\activate on Windows
  pip install -r requirements.txt
  ```

### "Qdrant server not reachable"
**Problem:** Backend falling back to in-memory Qdrant
- **Solution (Optional):** Start Docker Qdrant
  ```bash
  docker run -d -p 6333:6333 qdrant/qdrant
  ```
  Then restart the backend. Otherwise, in-memory mode works fine for development.

---

## 🧠 Key Technologies

### Backend
- **FastAPI** — Modern, fast web framework
- **Groq** — Fast LLM inference API
- **Qdrant** — Vector database with RBAC support
- **Sentence-Transformers** — Dense embeddings
- **PyMuPDF** — PDF parsing
- **Python-Jose** — JWT authentication

### Frontend
- **Next.js 15** — React framework with SSR
- **React 19** — UI library
- **Axios** — HTTP client
- **CSS** — Styling

---

## 📊 Performance Notes

- **First Query:** 30-60 seconds (models loading on first use)
- **Subsequent Queries:** 5-10 seconds (model caching)
- **Document Ingestion:** 5-15 minutes for 91 chunks
- **Qdrant Storage:** ~500MB for full medical dataset

---

## 🔒 Security Notes

- 🔐 JWT tokens expire after 24 hours
- 🔐 RBAC filtering at query level (not post-retrieval)
- 🔐 API keys stored in `.env` (not in code)
- ⚠️ CORS enabled for localhost (restrict in production)

---

## 📖 Documentation

- [BUILD_COMPLETE.md](BUILD_COMPLETE.md) — What's been implemented
- [SETUP.md](SETUP.md) — Detailed setup guide
- [implementation_plan.md](implementation_plan.md) — Architecture & design

---

## 🐛 Known Limitations

- Qdrant server not required (uses in-memory if Docker unavailable)
- SQL RAG limited to billing_executive and admin roles
- Demo database has placeholder data (not real medical records)
- Frontend hydration warnings on Chrome with extensions

---

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Sentence-Transformers](https://www.sbert.net/)
- [Next.js Documentation](https://nextjs.org/docs)

---

## 🤝 Contributing

This is a training project for MediBot. To contribute:

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -m "Add your feature"`
3. Push to branch: `git push origin feature/your-feature`
4. Open a Pull Request

---

## 📝 License

This project is part of the MediAssist Health Network training program.

---

## 💬 Support

For issues or questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review [SETUP.md](SETUP.md) for setup issues
3. Check backend logs at `http://localhost:8000/docs`


