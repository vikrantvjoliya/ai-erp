# Current System Architecture - ERP RAG System

**Last Updated:** December 6, 2025  
**Status:** Production-ready with ChromaDB integration

## 🏗️ System Overview

```
┌───────────────────────────────────────────────────────────────────┐
│                    ERP MODERNIZATION RAG SYSTEM                    │
│               ChromaDB + FastAPI + React Architecture              │
└───────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Input Documents → Data Ingestion → HuggingFace Embeddings        │
│                                            ↓                        │
│                               ╔═══════════════════════╗             │
│                               ║  ChromaDB (Persisted) ║             │
│                               ║  ./data/chromadb/     ║             │
│                               ║                       ║             │
│                               ║  • Document chunks    ║             │
│                               ║  • Vector embeddings  ║             │
│                               ║  • Metadata           ║             │
│                               ║  • Collection stats   ║             │
│                               ╚═══════════════════════╝             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND LAYER (Python)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              FastAPI Server (api_server.py)                  │  │
│  │              Port: 8000                                      │  │
│  │                                                              │  │
│  │  Endpoints:                                                  │  │
│  │  • /api/v1/chat          - Chat with model selection        │  │
│  │  • /api/v1/query         - Advanced RAG queries             │  │
│  │  • /api/v1/batch-query   - Multiple questions               │  │
│  │  • /api/value-streams    - Get value streams from ChromaDB  │  │
│  │  • /api/health-scores    - Health metrics                   │  │
│  │  • /api/kpis             - KPI extraction                   │  │
│  │  • /api/v1/statistics    - System statistics                │  │
│  │  • /api/models           - Available models                 │  │
│  └────────────────────┬─────────────────────────────────────────┘  │
│                       │                                             │
│  ┌────────────────────┴─────────────────────────────────────────┐  │
│  │        ERPHealthCheckPipeline (pipeline.py)                  │  │
│  │                                                              │  │
│  │  • query_knowledge_base()  - RAG or vector search           │  │
│  │  • ask_question()          - Simple Q&A                     │  │
│  │  • run_full_analysis()     - Complete pipeline              │  │
│  │  • _init_rag_system()      - Lazy RAG initialization        │  │
│  └────────┬─────────────────────────────────┬──────────────────┘  │
│           │                                  │                     │
│  ┌────────▼──────────────────┐  ┌──────────▼───────────────────┐  │
│  │  ChromaDataExtractor      │  │     RAGSystem                │  │
│  │  (chroma_data_extractor)  │  │  (rag_system_updated.py)     │  │
│  │                           │  │                               │  │
│  │  • get_value_streams()    │  │  • query()                   │  │
│  │  • get_health_scores()    │  │  • chat()                    │  │
│  │  • get_kpis()             │  │  • batch_query()             │  │
│  │  • get_document_count()   │  │  • _load_llm()               │  │
│  │  • _calculate_health()    │  │  • _format_sources()         │  │
│  └────────┬──────────────────┘  └──────────┬───────────────────┘  │
│           │                                  │                     │
│           └──────────────┬───────────────────┘                     │
│                          │                                         │
│  ┌───────────────────────▼──────────────────────────────────────┐  │
│  │              VectorStore (vector_store.py)                   │  │
│  │                                                              │  │
│  │  • create_vectorstore()   - Build from documents            │  │
│  │  • load_vectorstore()     - Load from disk                  │  │
│  │  • similarity_search()    - Vector search                   │  │
│  │  • search_by_category()   - Filtered search                 │  │
│  │  • get_collection_stats() - Statistics                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   FRONTEND LAYER (React + TypeScript)               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              React Application (UI/src/)                     │  │
│  │              Port: 3000                                      │  │
│  │                                                              │  │
│  │  Pages (Routes):                                             │  │
│  │  • /                - Dashboard with RagInsights            │  │
│  │  • /aichat          - AI Chat with model selection          │  │
│  │  • /knowledgebase   - Advanced search interface             │  │
│  │  • /insights        - Analysis jobs & monitoring            │  │
│  │  • /reports         - Generated reports                     │  │
│  │  • /riskheatmap     - Risk visualizations                   │  │
│  │                                                              │  │
│  │  Key Components:                                             │  │
│  │  • AIChat.tsx           - Chat interface                    │  │
│  │  • KnowledgeBase.tsx    - Search & browse                   │  │
│  │  • Dashboard.tsx        - Main dashboard                    │  │
│  │  • RagInsights.tsx      - AI insights widget                │  │
│  │  • ModelSelector.tsx    - Model dropdown                    │  │
│  │  • Header.tsx           - Navigation                        │  │
│  │                                                              │  │
│  │  Services:                                                   │  │
│  │  • api.ts               - TypeScript API client             │  │
│  │                                                              │  │
│  │  Contexts:                                                   │  │
│  │  • ModelContext.tsx     - Global model state                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 📂 Current File Structure

```
c:\rag-project\
│
├── 🐍 Backend (Python)
│   ├── api_server.py              # FastAPI server with all endpoints
│   ├── pipeline.py                # Main orchestration pipeline
│   ├── rag_system_updated.py      # RAG implementation
│   ├── chroma_data_extractor.py   # ChromaDB data extraction
│   ├── vector_store.py            # ChromaDB vector store wrapper
│   ├── text_processor.py          # Document chunking
│   ├── data_ingestion.py          # Document ingestion
│   ├── config.py                  # Configuration management
│   ├── config.yaml                # Settings file
│   ├── requirements.txt           # Python dependencies
│   │
│   ├── process_mining.py          # Process analysis
│   ├── sentiment_analysis.py      # Sentiment scoring
│   ├── benchmarking.py            # KPI gap analysis
│   ├── risk_assessment.py         # Risk evaluation
│   └── visualization.py           # Chart generation
│
├── ⚛️ Frontend (React + TypeScript)
│   └── UI/
│       ├── package.json
│       ├── tsconfig.json
│       ├── public/
│       └── src/
│           ├── App.tsx            # Main app with routing
│           ├── index.tsx          # Entry point
│           │
│           ├── pages/
│           │   ├── Dashboard.tsx        # Main dashboard
│           │   ├── AIChat.tsx           # Chat interface ⭐
│           │   ├── KnowledgeBase.tsx    # Search interface ⭐
│           │   ├── Insights.tsx         # Analysis jobs
│           │   ├── Reports.tsx          # Reports page
│           │   └── RiskHeatMap.tsx      # Risk viz
│           │
│           ├── components/
│           │   ├── RagInsights.tsx      # AI insights widget ⭐
│           │   ├── ModelSelector.tsx    # Model dropdown ⭐
│           │   ├── Header.tsx           # Navigation
│           │   ├── SystemStatistics.tsx # Stats display
│           │   └── ...
│           │
│           ├── contexts/
│           │   └── ModelContext.tsx     # Model state ⭐
│           │
│           ├── services/
│           │   └── api.ts               # API client ⭐
│           │
│           └── types/
│               └── index.ts             # TypeScript types
│
├── 📊 Data
│   ├── input/                     # Source documents (PDF, DOCX, etc.)
│   ├── output/                    # Generated reports
│   └── chromadb/                  # Vector store (persisted)
│
└── 📚 Documentation
    ├── README.md                  # Main README
    ├── ARCHITECTURE_CHROMADB.md   # ChromaDB architecture
    ├── RAG_INTEGRATION_SUMMARY.md # RAG integration guide
    ├── CHROMADB_INTEGRATION_COMPLETE.md
    ├── QUICKSTART.md
    └── DEPLOYMENT.md
```

## 🔄 Data Flow - Complete Walkthrough

### 1. Chat Request Flow (AIChat.tsx → Backend)

```
┌─────────────────────────────────────────────────────────────────┐
│ USER ACTION: Types question in AIChat                           │
│ "What are the main security risks?"                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: AIChat.tsx                                            │
│ • Get question from input                                       │
│ • Get model from ModelContext (vector-search/openai/ollama)    │
│ • Get useLLM from ModelContext (true/false)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ API CLIENT: sendChatMessage(question, model, useLLM)           │
│ POST http://localhost:8000/api/v1/chat                         │
│ Body: {                                                         │
│   "question": "What are the main security risks?",             │
│   "model": "vector-search",                                    │
│   "use_llm": false                                             │
│ }                                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASTAPI: @app.post("/api/v1/chat")                             │
│ • Validate input (length, not empty)                           │
│ • Load vector store if not loaded                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ VECTOR SEARCH: pipeline.vector_store.similarity_search()       │
│ • Search ChromaDB for relevant documents                       │
│ • Query: "What are the main security risks?"                   │
│ • top_k: 5                                                     │
│ • Returns: List[Document] with content + metadata              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ CONTEXT BUILDING                                                │
│ • Extract page_content from top 3 documents                    │
│ • Truncate to 800 chars each                                   │
│ • Join with newlines                                            │
│ • context = "\n\n".join([doc.page_content[:800] for docs])    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ ANSWER GENERATION                                               │
│                                                                 │
│ If use_llm = true AND model != "vector-search":                │
│    ├─→ model="openai"     → _generate_with_openai()           │
│    ├─→ model="ollama"     → _generate_with_ollama()           │
│    ├─→ model="huggingface"→ _generate_with_huggingface()      │
│    └─→ On error: Fallback to vector search                    │
│                                                                 │
│ Else (vector-search mode):                                     │
│    • Format context from retrieved documents                   │
│    • answer = "Based on documentation:\n" + formatted_context  │
│    • model_used = "vector-search"                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ RESPONSE FORMATTING                                             │
│ {                                                               │
│   "question": "What are the main security risks?",             │
│   "answer": "Based on the available documentation:...",        │
│   "timestamp": "2025-12-06T10:30:00",                          │
│   "status": "success",                                          │
│   "model_used": "vector-search",                               │
│   "sources_count": 5                                            │
│ }                                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Display Message                                      │
│ • Add to messages array                                         │
│ • Show in chat interface                                        │
│ • Display timestamp                                             │
│ • Scroll to bottom                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Knowledge Base Query Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ USER ACTION: Enters search in KnowledgeBase                    │
│ • Query: "compliance requirements"                              │
│ • Filters: category="Security", top_k=10, use_rag=true        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ API CLIENT: queryKnowledgeBase(query, category, topK, useRAG)  │
│ POST http://localhost:8000/api/v1/query                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASTAPI: @app.post("/api/v1/query")                            │
│ • Validate request                                              │
│ • Call pipeline.query_knowledge_base()                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PIPELINE: query_knowledge_base()                                │
│                                                                 │
│ If use_rag = true:                                             │
│    ├─→ Initialize RAGSystem (lazy load)                        │
│    ├─→ rag_system.query(query, return_source=True)            │
│    │    ├─→ Vector search for context                          │
│    │    ├─→ LLM generates intelligent answer                   │
│    │    └─→ Format sources                                     │
│    └─→ Return {query, answer, sources[]}                       │
│                                                                 │
│ Else (use_rag = false):                                        │
│    ├─→ vector_store.similarity_search()                        │
│    │    or search_by_category() if category provided           │
│    └─→ Return documents only                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ RESPONSE                                                        │
│ {                                                               │
│   "query": "compliance requirements",                           │
│   "answer": "Based on the analysis, key compliance...",        │
│   "category": "Security",                                       │
│   "sources": [                                                  │
│     {                                                           │
│       "index": 1,                                               │
│       "source": "security_audit.pdf",                           │
│       "category": "Security",                                   │
│       "content_preview": "Compliance requirements include..."  │
│     }                                                           │
│   ],                                                            │
│   "results_count": 10,                                          │
│   "use_rag": true                                               │
│ }                                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: KnowledgeBase.tsx                                    │
│ • Display AI answer in cyan card                               │
│ • Render source documents as expandable cards                  │
│ • Show category, source file, content preview                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Dashboard Data Flow (Value Streams & Health Scores)

```
┌─────────────────────────────────────────────────────────────────┐
│ DASHBOARD LOADS: useEffect(() => {}, [])                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ├───────────────────────┬──────────────┐
                           ↓                       ↓              ↓
                    getValueStreams()    getHealthScores()   getKPIs()
                           │                       │              │
                           ↓                       ↓              ↓
                 /api/value-streams      /api/health-scores  /api/kpis
                           │                       │              │
                           ↓                       ↓              ↓
              data_extractor.          data_extractor.    data_extractor.
              get_value_streams()      get_health_scores() get_kpis()
                           │                       │              │
                           ↓                       ↓              ↓
                    ┌────────────────────────────────────────────────┐
                    │    ChromaDB Collection                         │
                    │                                                │
                    │  • Query metadata for value streams            │
                    │  • Query documents by vs_code for health       │
                    │  • Pattern match content for KPIs              │
                    └────────────────────────────────────────────────┘
                           │
                           ↓
                    ┌────────────────────────────────────────────────┐
                    │ RETURN DATA                                    │
                    │                                                │
                    │ Value Streams: [{code, name}, ...]            │
                    │ Health Scores: [{vs_code, process_health,     │
                    │                  system_health, ...}, ...]     │
                    │ KPIs: [{vs_code, kpi_name, current_value,     │
                    │         target_value, ...}, ...]               │
                    └────────────────────────────────────────────────┘
                           │
                           ↓
                    ┌────────────────────────────────────────────────┐
                    │ RENDER DASHBOARD                               │
                    │ • Value stream selector                        │
                    │ • Health score cards                           │
                    │ • KPI tables                                   │
                    │ • Charts and visualizations                    │
                    │ • RagInsights widget (batch query)             │
                    └────────────────────────────────────────────────┘
```

### 4. RagInsights Widget Flow (Batch Query)

```
┌─────────────────────────────────────────────────────────────────┐
│ COMPONENT MOUNT: RagInsights.tsx useEffect()                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ BATCH QUERY: batchQuery(queries[])                             │
│ queries = [                                                     │
│   "What is the overall readiness score and what does it mean?",│
│   "What are the top 3 critical risks identified?",             │
│   "What modernization steps should be prioritized?"            │
│ ]                                                               │
│                                                                 │
│ POST http://localhost:8000/api/v1/batch-query                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASTAPI: @app.post("/api/v1/batch-query")                      │
│ • Iterate through queries                                       │
│ • For each: pipeline.query_knowledge_base(query, use_rag=True) │
│ • Collect results                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ RESPONSE                                                        │
│ {                                                               │
│   "results": [                                                  │
│     {                                                           │
│       "question": "What is the overall readiness score...",    │
│       "answer": "The readiness score is 75%, indicating..."    │
│     },                                                          │
│     {                                                           │
│       "question": "What are the top 3 critical risks...",      │
│       "answer": "1. Security vulnerabilities... 2. Data..."    │
│     },                                                          │
│     {                                                           │
│       "question": "What modernization steps...",               │
│       "answer": "Priority 1: Address security gaps..."         │
│     }                                                           │
│   ],                                                            │
│   "total_queries": 3,                                           │
│   "timestamp": "2025-12-06T10:30:00"                           │
│ }                                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ RENDER INSIGHTS                                                 │
│ • 3 cards with icons (info, risk, success)                     │
│ • Card 1 (blue): Readiness interpretation                      │
│ • Card 2 (red): Critical risks                                 │
│ • Card 3 (green): Prioritized steps                            │
│ • Refresh button to regenerate                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🔑 Key Features & Current State

### ✅ Fully Implemented Features

#### Backend
- [x] **FastAPI Server** - REST API with CORS support
- [x] **ChromaDB Integration** - Vector store with persistence
- [x] **RAG System** - Query with LLM generation
- [x] **Model Support** - Vector-search, OpenAI, Ollama, HuggingFace
- [x] **Data Extraction** - Automatic value streams, health scores, KPIs
- [x] **Batch Queries** - Multiple questions in one call
- [x] **Health Check** - System status endpoint
- [x] **Statistics** - Document counts and metrics
- [x] **Error Handling** - Graceful fallbacks and error messages
- [x] **Lazy Loading** - RAG system initialized on-demand
- [x] **Caching** - Value streams and health scores cached

#### Frontend
- [x] **React Router** - Page navigation (Dashboard, AI Chat, etc.)
- [x] **AI Chat Interface** - Model selection, LLM toggle, batch queries
- [x] **Knowledge Base** - Advanced search with filters
- [x] **Dashboard** - Value streams, health scores, KPI display
- [x] **RagInsights Widget** - Auto-generated AI insights
- [x] **ModelContext** - Global state for model selection
- [x] **TypeScript API Client** - Full type safety
- [x] **Responsive UI** - Tailwind CSS styling
- [x] **Animations** - Framer Motion transitions
- [x] **Error States** - User-friendly error messages
- [x] **Loading States** - Spinners and skeletons

### 🎯 Model Selection System

Current implementation supports:

1. **Vector-Search** (Default - Recommended)
   - Fast similarity search without LLM
   - Returns context from ChromaDB
   - No API keys required
   - Best performance

2. **OpenAI** (Optional)
   - Requires OPENAI_API_KEY environment variable
   - Uses GPT models for intelligent answers
   - Higher quality responses
   - Costs per request

3. **Ollama** (Optional)
   - Requires local Ollama installation
   - Free, local LLM inference
   - Good quality, privacy-preserving
   - Requires setup

4. **HuggingFace** (Optional)
   - Uses local transformer models
   - Free, but requires GPU for speed
   - Configurable model in config.yaml
   - Higher memory usage

## 📊 API Endpoints Reference

### Chat & Query Endpoints

| Endpoint | Method | Purpose | Request Body | Response |
|----------|--------|---------|--------------|----------|
| `/api/v1/chat` | POST | Chat with model selection | `{question, model, use_llm}` | `{question, answer, timestamp, model_used}` |
| `/api/v1/query` | POST | Advanced RAG query | `{query, category, top_k, use_rag}` | `{query, answer, sources[], results_count}` |
| `/api/v1/batch-query` | POST | Multiple questions | `{queries[], category}` | `{results[], total_queries}` |

### Data Endpoints

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/value-streams` | GET | Get value streams from ChromaDB | `[{code, name}, ...]` |
| `/api/health-scores` | GET | All health scores | `[{vs_code, process_health, ...}, ...]` |
| `/api/health-scores/{vs}` | GET | Specific value stream health | `{vs_code, process_health, ...}` |
| `/api/kpis` | GET | All KPIs (optional ?vs_code filter) | `[{vs_code, kpi_name, ...}, ...]` |
| `/api/v1/statistics` | GET | System statistics | `{document_count, collection_name, ...}` |
| `/api/models` | GET | Available models | `{vector-search: {...}, openai: {...}}` |

### System Endpoints

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/health` | GET | Health check | `{status, pipeline_initialized, ...}` |
| `/` | GET | API info | `{name, version, endpoints}` |
| `/docs` | GET | Swagger UI | Interactive API docs |

## 🛠️ Configuration

### Backend (`config.yaml`)

```yaml
model:
  llm_provider: huggingface
  llm_model: mistralai/Mistral-7B-Instruct-v0.2
  llm_device: cpu  # or 'cuda' for GPU
  embedding_model: sentence-transformers/all-MiniLM-L6-v2
  embedding_device: cpu
  load_in_8bit: false

vector_store:
  persist_directory: ./data/chromadb
  collection_name: erp_modernization
  top_k: 5
  score_threshold: 0.7

chunking:
  chunk_size: 1000
  chunk_overlap: 200

api:
  host: 0.0.0.0
  port: 8000
  enable_cors: true
  cors_origins:
    - "http://localhost:3000"

analysis:
  enable_rag: true
```

### Frontend (Environment Variables)

```bash
# .env file
REACT_APP_API_URL=http://localhost:8000/api
```

## 🚀 Setup & Usage

### Initial Setup

```powershell
# 1. Backend setup
cd c:\rag-project
python -m venv env
.\env\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Ingest documents
python data_ingestion.py

# 3. Start backend
python api_server.py

# 4. Start frontend (new terminal)
cd UI
npm install
npm start
```

### Daily Usage

```powershell
# Terminal 1: Backend
cd c:\rag-project
.\env\Scripts\Activate.ps1
python api_server.py

# Terminal 2: Frontend
cd c:\rag-project\UI
npm start

# Access at http://localhost:3000
```

## 🔍 Troubleshooting

### "Vector store not found"
```powershell
python data_ingestion.py
```

### "Cannot connect to server"
```powershell
# Check backend is running
curl http://localhost:8000/health
```

### Slow responses
```yaml
# Use vector-search model (no LLM)
# In UI: Select "Vector Search Only" from model dropdown
```

## 📈 Performance Metrics

| Operation | Response Time | Notes |
|-----------|---------------|-------|
| Vector search | <100ms | Fast, recommended |
| RAG with HuggingFace | 2-5s | Requires GPU for speed |
| Health score calculation | <200ms | Cached after first call |
| Value stream extraction | <50ms | Cached |
| Batch query (3 questions) | 6-15s | 3x individual queries |

## ✨ Recent Updates

**December 6, 2025:**
- ✅ Renamed AIChat_new.tsx → AIChat.tsx
- ✅ Integrated ModelContext for global model state
- ✅ Added model selection in chat interface
- ✅ Implemented batch query modal in AIChat
- ✅ Updated all documentation to reflect current file names
- ✅ Verified ChromaDB integration with all endpoints
- ✅ Confirmed RagInsights widget working with batch queries

---

**This document reflects the actual current state of the codebase as of December 6, 2025.**
