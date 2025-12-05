# ERP Health Check - RAG Integration Architecture

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE (React)                             │
│                          http://localhost:3000                               │
└────────────┬────────────────────────────────────────────────────────────────┘
             │
             │  REST API Calls (JSON)
             │
┌────────────▼────────────────────────────────────────────────────────────────┐
│                    NAVIGATION BAR                                            │
│  Dashboard | Value Stream | AI Assistant | Knowledge Base | Insights | Reports│
└─────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴────────┘
      │             │              │              │              │
      │             │              │              │              │
┌─────▼─────┐ ┌────▼────┐ ┌──────▼──────┐ ┌────▼──────┐ ┌────▼─────┐
│ Dashboard │ │  Risk   │ │  AI Chat    │ │ Knowledge │ │ Insights │
│           │ │ HeatMap │ │             │ │   Base    │ │          │
│ • Metrics │ │         │ │ • Chat UI   │ │           │ │ • Charts │
│ • Charts  │ │ • Heat  │ │ • Messages  │ │ • Search  │ │ • KPIs   │
│ • RAG     │ │   Maps  │ │ • Sources   │ │ • Filters │ │          │
│   Insights│ │ • Risk  │ │ • Suggested │ │ • Results │ │          │
│   Widget  │ │   Table │ │   Questions │ │ • Sources │ │          │
└───────────┘ └─────────┘ └─────────────┘ └───────────┘ └──────────┘
      │             │              │              │              │
      └─────────────┴──────────────┴──────────────┴──────────────┘
                                   │
                        TypeScript API Service
                              (api.ts)
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      │                            │                            │
      ▼                            ▼                            ▼
 queryKnowledgeBase()       sendChatMessage()           batchQuery()
      │                            │                            │
      └────────────────────────────┴────────────────────────────┘
                                   │
                             HTTP Requests
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FASTAPI SERVER (Python)                                  │
│                     http://localhost:8000                                    │
│                         (api_server.py)                                      │
└────────────┬────────────────────────────────────────────────────────────────┘
             │
             │  Routes & Endpoints
             │
    ┌────────┼────────┬────────────────────────────┐
    │        │        │                            │
    ▼        ▼        ▼                            ▼
┌────────┐ ┌────────┐ ┌──────────────────┐ ┌──────────────┐
│/v1/chat│ │/v1/query│ │/v1/batch-query   │ │  /health     │
│        │ │         │ │                  │ │  /config     │
│Simple  │ │Advanced │ │Multiple          │ │  /status     │
│Q&A     │ │Search   │ │Questions         │ │  /reports    │
└────┬───┘ └────┬────┘ └─────┬────────────┘ └──────────────┘
     │          │             │
     └──────────┴─────────────┘
                │
                │  Calls Pipeline Methods
                │
                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   PIPELINE (pipeline.py)                                     │
│                   ERPHealthCheckPipeline                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  • query_knowledge_base(query, category, top_k, use_rag)                   │
│  • ask_question(question)                                                   │
│  • _init_rag_system()                                                       │
│                                                                              │
└────────────┬────────────────────────────────────────────────────────────────┘
             │
             │  Initializes & Uses
             │
    ┌────────┼────────┐
    │        │        │
    ▼        ▼        ▼
┌────────────────┐ ┌───────────────┐ ┌──────────────────┐
│  RAG SYSTEM    │ │ VECTOR STORE  │ │ TEXT PROCESSOR   │
│                │ │               │ │                  │
│ (rag_system_   │ │ (vector_store │ │ (text_processor  │
│  updated.py)   │ │  .py)         │ │  .py)            │
├────────────────┤ ├───────────────┤ ├──────────────────┤
│                │ │               │ │                  │
│ • query()      │ │ • ChromaDB    │ │ • Chunking       │
│ • chat()       │ │ • Embeddings  │ │ • Cleaning       │
│ • batch_query()│ │ • Similarity  │ │ • Metadata       │
│ • _format_     │ │   Search      │ │                  │
│   sources()    │ │ • Filtering   │ │                  │
│                │ │               │ │                  │
└────┬───────────┘ └───────┬───────┘ └──────────────────┘
     │                     │
     │                     │
     ▼                     ▼
┌──────────────────────────────────────────┐
│         HUGGING FACE MODELS              │
├──────────────────────────────────────────┤
│                                          │
│  LLM (Language Model):                   │
│  • Mistral-7B-Instruct                  │
│  • Llama-2-7b-chat                      │
│  • Flan-T5-base                         │
│                                          │
│  Embeddings:                             │
│  • all-MiniLM-L6-v2                     │
│  • all-mpnet-base-v2                    │
│                                          │
└──────────────────────────────────────────┘


## Data Flow Diagram

USER QUERY FLOW:
================

1. User enters question in UI
       │
       ▼
2. React sends POST to /api/v1/chat or /api/v1/query
       │
       ▼
3. FastAPI receives request, validates input
       │
       ▼
4. Pipeline.query_knowledge_base() called
       │
       ├─► IF use_rag=True:
       │   │
       │   ├─► Initialize RAG System (if needed)
       │   │   └─► Load LLM and Embedding Models
       │   │
       │   ├─► Vector Store Retrieval
       │   │   └─► ChromaDB searches for relevant documents
       │   │       └─► Returns top K documents (default: 5)
       │   │
       │   ├─► RAG System Processing
       │   │   ├─► Format documents as context
       │   │   ├─► Create prompt with context + question
       │   │   ├─► Send to LLM
       │   │   └─► LLM generates intelligent answer
       │   │
       │   └─► Format Response
       │       ├─► Answer text
       │       ├─► Source documents
       │       └─► Metadata
       │
       └─► IF use_rag=False:
           └─► Simple Vector Search
               └─► Return matching documents only
       │
       ▼
5. FastAPI formats JSON response
       │
       ▼
6. React receives response
       │
       ▼
7. UI displays answer and sources


## Component Interaction Matrix

┌──────────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│              │ AI Chat  │Knowledge │Dashboard │ RAG      │ Vector   │
│              │          │   Base   │ Insights │ System   │  Store   │
├──────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ AI Chat      │    -     │    ✗     │    ✗     │    ✓     │    ✓     │
├──────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Knowledge    │    ✗     │    -     │    ✗     │    ✓     │    ✓     │
│ Base         │          │          │          │          │          │
├──────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Dashboard    │    ✗     │    ✗     │    -     │    ✓     │    ✓     │
│ Insights     │          │          │          │          │          │
├──────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ RAG System   │    ✓     │    ✓     │    ✓     │    -     │    ✓     │
├──────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Vector Store │    ✓     │    ✓     │    ✓     │    ✓     │    -     │
└──────────────┴──────────┴──────────┴──────────┴──────────┴──────────┘

Legend: ✓ = Uses, ✗ = No direct interaction


## File Structure

```
c:\rag-project\
│
├── Backend (Python)
│   ├── api_server.py              ← FastAPI server with RAG endpoints
│   ├── pipeline.py                ← Orchestration with RAG methods
│   ├── rag_system_updated.py      ← Core RAG implementation ⭐
│   ├── vector_store.py            ← ChromaDB integration
│   ├── text_processor.py          ← Document processing
│   ├── config.py                  ← Configuration management
│   ├── config.yaml                ← Settings (models, parameters)
│   └── requirements.txt           ← Python dependencies
│
├── Frontend (React/TypeScript)
│   └── src/
│       ├── pages/
│       │   ├── AIChat_new.tsx     ← Chat interface ⭐
│       │   ├── KnowledgeBase.tsx  ← Search interface ⭐
│       │   ├── Dashboard.tsx      ← Modified with insights
│       │   └── ...
│       ├── components/
│       │   ├── RagInsights.tsx    ← Dashboard widget ⭐
│       │   └── ...
│       ├── services/
│       │   └── api.ts             ← API integration ⭐
│       └── App.tsx                ← Modified with KB route
│
├── Data
│   ├── chromadb/                  ← Vector store database
│   ├── input/                     ← Source documents
│   └── output/                    ← Generated reports
│
├── Documentation
│   ├── RAG_INTEGRATION_GUIDE.md   ← Complete guide ⭐
│   ├── RAG_INTEGRATION_SUMMARY.md ← Summary doc ⭐
│   └── README.md                  ← Main README
│
└── Scripts
    ├── quickstart_rag.ps1         ← Setup script ⭐
    └── start_services.ps1         ← Service launcher ⭐

⭐ = New/Significantly Modified for RAG Integration
```

## Technology Stack

### Backend
```
┌─────────────────────────────────────┐
│ Python 3.8+                         │
│ ├─ FastAPI (Web Framework)         │
│ ├─ LangChain (RAG Framework)       │
│ ├─ HuggingFace (Models)            │
│ │  ├─ Transformers                 │
│ │  └─ Sentence Transformers        │
│ ├─ ChromaDB (Vector Database)      │
│ └─ Loguru (Logging)                │
└─────────────────────────────────────┘
```

### Frontend
```
┌─────────────────────────────────────┐
│ React 18                            │
│ ├─ TypeScript                       │
│ ├─ Framer Motion (Animations)      │
│ ├─ Lucide React (Icons)            │
│ ├─ TailwindCSS (Styling)           │
│ └─ Axios (HTTP Client)             │
└─────────────────────────────────────┘
```

## Deployment Architecture

```
Development:
┌────────────────────┐  ┌────────────────────┐
│  Backend Server    │  │  Frontend Server   │
│  localhost:8000    │◄─┤  localhost:3000    │
│  (Python/FastAPI)  │  │  (React Dev)       │
└────────────────────┘  └────────────────────┘
         │
         ▼
┌────────────────────┐
│   Vector Store     │
│   (ChromaDB)       │
│   ./data/chromadb  │
└────────────────────┘

Production (Example):
┌────────────────────┐  ┌────────────────────┐
│  API Server        │  │  Web Server        │
│  api.example.com   │◄─┤  app.example.com   │
│  (Docker/K8s)      │  │  (Nginx/React)     │
└────────────────────┘  └────────────────────┘
         │
         ▼
┌────────────────────┐
│  Persistent Store  │
│  (Volume/S3)       │
└────────────────────┘
```

## Performance Characteristics

```
Operation              | Avg Time  | Scalability
──────────────────────┼───────────┼──────────────
Vector Search         | <1 sec    | Excellent
RAG Query (CPU)       | 2-5 sec   | Good
RAG Query (GPU)       | 0.5-2 sec | Excellent
Batch Query (3x)      | 6-15 sec  | Good
Index Creation        | 1-5 min   | One-time
UI Response Time      | <100 ms   | Excellent
API Latency           | <50 ms    | Excellent
```

## Security Model

```
┌─────────────────────────────────────┐
│         Security Layers             │
├─────────────────────────────────────┤
│ 1. Input Validation                 │
│    ├─ FastAPI Pydantic Models      │
│    └─ TypeScript Type Checking     │
├─────────────────────────────────────┤
│ 2. CORS Configuration               │
│    └─ Allowed Origins List         │
├─────────────────────────────────────┤
│ 3. Data Privacy                     │
│    ├─ Local Processing Only        │
│    ├─ No External APIs             │
│    └─ Self-Hosted Models           │
├─────────────────────────────────────┤
│ 4. Error Handling                   │
│    ├─ Safe Error Messages          │
│    └─ No Internal Info Exposure    │
└─────────────────────────────────────┘
```

## Scalability Options

```
Current Setup (Single Machine):
┌──────────────────────────────────┐
│ Backend + Frontend + Vector DB   │
│ ~ 8-16GB RAM, 4+ CPU cores       │
└──────────────────────────────────┘

Scaled Setup (Multiple Machines):
┌────────────┐  ┌────────────┐  ┌────────────┐
│ Load       │  │ API Server │  │ Vector DB  │
│ Balancer   │─►│ Cluster    │─►│ Cluster    │
└────────────┘  └────────────┘  └────────────┘
                      │
                      ▼
                ┌────────────┐
                │ Model      │
                │ Inference  │
                │ Service    │
                └────────────┘
```

---

This diagram provides a complete visual reference for understanding how all components work together in the RAG-integrated ERP Health Check system.
