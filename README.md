# AskDocs AI 🤖📄

> **AI-Powered Semantic Document Q&A System**  
> Upload your PDFs and ask questions in natural language — get accurate answers with source citations.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-askdoc--ai--deploy.onrender.com-blue?style=for-the-badge)](https://askdoc-ai-deploy.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square&logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green?style=flat-square&logo=django)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---


---

## ✨ Features

- 📤 **PDF Upload** — Upload any PDF document (up to 10MB)
- 🔍 **Semantic Search** — Finds meaning-based matches, not just keywords
- 🤖 **AI-Powered Answers** — Groq Llama 3 generates fluent, accurate responses
- 📌 **Source Citations** — Every answer includes document name and page number
- 🔐 **JWT Authentication** — Secure login/register with role-based access
- 🎨 **3 Themes** — Dark, Light, and Rose modes
- 📱 **Responsive UI** — Works on desktop and mobile
- 🗂️ **Multi-document** — Upload and query multiple PDFs simultaneously
- 🧹 **Clear History** — Manage your chat and document history

---

## 🧠 How It Works

```
User uploads PDF
      ↓
System extracts & chunks text
      ↓
Text converted to vector embeddings
(sentence-transformers/all-MiniLM-L6-v2)
      ↓
Embeddings stored in FAISS index
      ↓
User asks a question
      ↓
Question converted to embedding
      ↓
FAISS retrieves top 15 relevant chunks
      ↓
Cross-encoder reranks top 8 chunks
      ↓
Groq Llama 3 generates final answer
      ↓
Answer + source citations displayed
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 5.2 + Django REST Framework |
| **Database** | PostgreSQL |
| **Authentication** | JWT (djangorestframework-simplejwt) |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) |
| **Vector Search** | FAISS (Facebook AI Similarity Search) |
| **Reranking** | CrossEncoder (ms-marco-MiniLM-L-6-v2) |
| **LLM** | Groq API (Llama 3.1 8B Instant) |
| **PDF Parsing** | pdfplumber |
| **Frontend** | HTML + CSS + Vanilla JavaScript |
| **Deployment** | Render.com |

---

## 🚀 Live Demo

🌐 **[https://askdoc-ai-deploy.onrender.com](https://askdoc-ai-deploy.onrender.com)**

> ⚠️ **Note:** The free tier server sleeps after 15 minutes of inactivity.
> First visit may take 30–60 seconds to wake up. Please be patient!

### Demo Credentials
```
Username: demo
Password: Demo@12345
```
*(Or register your own free account)*

---

## 📦 Local Setup

### Prerequisites
- Python 3.10+
- PostgreSQL
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/Kshitij9137/AskDoc_AI-Deploy.git
cd AskDoc_AI-Deploy
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Create .env File
```bash
cp .env.example .env
```

Edit `.env` with your values:
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_NAME=askdocs_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
DATABASE_HOST=localhost
DATABASE_PORT=5432
GROQ_API_KEY=your-groq-api-key
```

Get a **free** Groq API key at [console.groq.com](https://console.groq.com)

### Step 5: Setup Database
```bash
# Create database in PostgreSQL first
createdb askdocs_db

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

### Step 6: Run Development Server
```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) 🎉

---

## 🗂️ Project Structure

```
AskDoc_AI-Deploy/
├── askdocs_backend/        # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── documents/              # Document handling app
│   ├── models.py           # Document, Chunk, Embedding models
│   ├── views.py            # Upload, list, delete APIs
│   ├── processor.py        # Full processing pipeline
│   ├── extractor.py        # PDF text extraction
│   ├── chunker.py          # Text chunking
│   ├── embedder.py         # Vector embeddings
│   └── faiss_store.py      # FAISS index management
├── qa_engine/              # Q&A system app
│   ├── models.py           # QueryLog, QuerySource models
│   ├── views.py            # Ask question API
│   ├── pipeline.py         # Full RAG pipeline
│   ├── searcher.py         # FAISS semantic search
│   └── llm.py              # Groq API integration
├── users/                  # Authentication app
│   ├── models.py           # CustomUser model
│   └── views.py            # Register, login, profile APIs
├── static/frontend/        # Frontend files
│   ├── index.html          # Main app page
│   ├── login.html          # Login page
│   ├── register.html       # Register page
│   ├── css/
│   │   ├── app.css         # Main styles
│   │   ├── style.css       # Auth page styles
│   │   └── theme.css       # Dark/Light/Rose themes
│   └── js/
│       ├── app.js          # Main app logic
│       ├── auth.js         # Authentication logic
│       └── theme.js        # Theme switching
├── .env.example            # Environment template
├── Procfile                # Render deployment config
├── render.yaml             # Render service config
├── requirements.txt        # Python dependencies
└── manage.py
```

---

## 🔌 API Endpoints

### Authentication
```
POST /api/auth/register/         Register new user
POST /api/auth/login/            Login → returns JWT tokens
GET  /api/auth/profile/          Get user profile
POST /api/auth/token/refresh/    Refresh access token
```

### Documents
```
POST /api/documents/upload/      Upload & process PDF
GET  /api/documents/             List user's documents
DELETE /api/documents/<id>/      Delete a document
```

### Q&A
```
POST /api/qa/ask/                Ask a question
GET  /api/qa/history/            Get chat history
DELETE /api/qa/history/clear/    Clear chat history
```

---

## 🌐 Deployment (Render.com)

### Environment Variables Required
```env
SECRET_KEY=<generate-new-key>
DEBUG=False
DATABASE_URL=<from-render-postgresql>
GROQ_API_KEY=<your-groq-key>
ALLOWED_HOSTS=your-app.onrender.com,localhost
CORS_ALLOWED_ORIGINS=https://your-app.onrender.com
PYTHON_VERSION=3.10.11
```

### Generate Secret Key
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## ⚠️ Known Limitations (Free Tier)

| Limitation | Details |
|------------|---------|
| Server sleeps | Wakes after 30–60s on first visit |
| FAISS resets | Re-upload documents after server restart |
| 512MB RAM | No local LLM — uses Groq API instead |
| 750 hrs/month | Enough for full month usage |

---

## 👨‍💻 Author

**Kshitij Gupta**  
MCA 4th Semester — University of Allahabad  
Enrollment: U2449028  

[![GitHub](https://img.shields.io/badge/GitHub-Kshitij9137-black?style=flat-square&logo=github)](https://github.com/Kshitij9137)

---

## 🙏 Acknowledgments

- [Groq](https://groq.com) — LLM API
- [Facebook FAISS](https://github.com/facebookresearch/faiss) — Vector search
- [Sentence Transformers](https://www.sbert.net) — Text embeddings
- [Render](https://render.com) — Hosting

---

---

<div align="center">
  <p>⭐ If you found this helpful, please star the repo!</p>
  <p>Made with ❤️ for MCA Final Semester Project</p>
</div>
