# Using ChromaDB Data for API Endpoints

## Overview
The backend now fetches data **directly from your ChromaDB vector store** instead of using sample parquet files. This means all value streams, health scores, and KPIs are extracted from your actual RAG documents!

## How It Works

### Data Flow
```
Your Documents → Data Ingestion → ChromaDB Vector Store → Data Extractor → API Endpoints → React UI
```

1. **Documents Ingested**: Your ERP documents are loaded and embedded into ChromaDB
2. **Metadata Extracted**: Value streams, categories, and document types stored in metadata
3. **Content Analyzed**: Document content is analyzed for KPIs, health indicators, and pain points
4. **Real-time Queries**: API endpoints query ChromaDB in real-time for fresh data

## Prerequisites

### 1. Ingest Your Documents First

Before the API endpoints can return data, you need to have documents in ChromaDB:

```powershell
cd c:\rag-project
.\env\Scripts\activate

# Run data ingestion to load documents into ChromaDB
python data_ingestion.py

# OR run the full pipeline
python pipeline.py
```

This will:
- Load all documents from `./data/input/`
- Extract text, metadata, and categories
- Create embeddings and store in ChromaDB
- Save vector store to `./chroma_db/` (or configured path)

### 2. Verify Vector Store Exists

Check that ChromaDB was created:

```powershell
# Check if vector store directory exists
Test-Path ./chroma_db

# Should show True if vector store was created
```

## Data Extraction from ChromaDB

### Value Streams
Extracted from document metadata fields:
- `metadata['value_stream']` - Primary field
- `metadata['vs_code']` - Alternative field
- `metadata['category']` - Fallback field
- Document filenames and content (pattern matching)

**Example metadata:**
```json
{
  "source": "O2C_Process_Document.pdf",
  "value_stream": "O2C",
  "category": "Order to Cash",
  "file_type": "pdf"
}
```

### Health Scores
Calculated dynamically by analyzing:
- **Document Count**: More docs = better coverage
- **Finding Count**: Issues, problems, errors mentioned
- **Pain Point Count**: Bottlenecks, challenges, risks identified
- **RAG Status**: Green/Yellow/Amber/Red based on scores

**Calculation Logic:**
```python
process_health = base_score - issue_penalty
system_health = base_score - (issue_penalty * 1.2)
readiness_score = (process_health + system_health) / 2
```

### KPIs
Extracted from document content using pattern matching:
- Performance metrics (rate, time, score, percentage)
- Target values mentioned in documents
- Cost and value metrics

**Patterns Detected:**
- "Order Fulfillment Rate: 85%"
- "KPI: Average Processing Time - 3.5 days"
- "Target: Customer Satisfaction Score - 92%"

## Starting the API Server

```powershell
cd c:\rag-project
.\env\Scripts\activate

# Start the API server
python api_server.py
```

**On Startup:**
1. Initializes ERP Health Check Pipeline
2. Attempts to load existing vector store from ChromaDB
3. Creates `ChromaDataExtractor` instance
4. Logs document count: "ChromaDB data extractor initialized with X documents"

**Expected Startup Logs:**
```
INFO: Initializing ERP Health Check Pipeline...
INFO: Vector store loaded from ./chroma_db
INFO: ChromaDB data extractor initialized with 127 documents
INFO: API Server ready!
```

## API Endpoints Using ChromaDB

### 1. Get Value Streams
```
GET /api/value-streams
```
Queries ChromaDB metadata to find unique value streams.

**Response:**
```json
{
  "value_streams": [
    {"code": "O2C", "name": "Order to Cash"},
    {"code": "P2P", "name": "Procure to Pay"}
  ]
}
```

### 2. Get Health Scores
```
GET /api/health-scores
GET /api/health-scores/{vs_code}
```
Analyzes documents per value stream to calculate health metrics.

**Response:**
```json
{
  "vs_code": "O2C",
  "process_health": 85.5,
  "system_health": 78.3,
  "readiness_score": 81.9,
  "value_at_stake_usd": 1500000,
  "rag_status": "Green",
  "kpi_count": 12,
  "finding_count": 25,
  "painpoint_count": 8
}
```

### 3. Get KPIs
```
GET /api/kpis?vs_code=O2C
```
Extracts KPIs from document content using NLP patterns.

**Response:**
```json
{
  "kpis": [
    {
      "vs_code": "O2C",
      "kpi_name": "Order Fulfillment Rate",
      "current_value": "82.5%",
      "target_value": "95.0%",
      "definition": "Measures order fulfillment rate for O2C process",
      "target_direction": "higher"
    }
  ]
}
```

### 4. System Statistics
```
GET /api/v1/statistics
```
Returns real-time stats including document count from ChromaDB.

**Response:**
```json
{
  "total_jobs": 5,
  "completed_jobs": 3,
  "vector_store": {
    "collection_name": "erp_docs",
    "persist_directory": "./chroma_db",
    "document_count": 127
  }
}
```

## Improving Data Quality

### 1. Add Metadata to Documents

When ingesting documents, ensure proper metadata:

```python
from data_ingestion import DataIngestionPipeline

pipeline = DataIngestionPipeline()

# Documents will have metadata auto-labeled
documents = pipeline.ingest_directory("./data/input")

# Or add custom metadata
for doc in documents:
    doc.metadata['value_stream'] = 'O2C'
    doc.metadata['document_type'] = 'process_map'
```

### 2. Organize Files by Value Stream

Structure your input directory:
```
data/input/
  O2C/
    order_processing.pdf
    invoice_management.xlsx
  P2P/
    procurement_flow.docx
    vendor_management.pdf
  R2R/
    financial_close.pdf
```

### 3. Include KPI Documents

Add documents that explicitly mention KPIs:
- Performance reports
- KPI dashboards (exported as PDF)
- Target definitions
- Metric documentation

## Troubleshooting

### No Value Streams Found
```
Error: "No value streams found in vector store"
```

**Solution:**
1. Check if vector store exists: `Test-Path ./chroma_db`
2. Check document count: Look for startup log
3. Re-run ingestion with proper metadata:
   ```powershell
   python data_ingestion.py
   ```

### Health Scores Return 404
```
Error: "Data not available. Run analysis and create vector store first."
```

**Solution:**
1. Ensure documents are ingested
2. Restart API server to reload vector store
3. Check logs for initialization errors

### KPIs Not Found
```
Error: "No KPIs found"
```

**Solution:**
1. Add documents with explicit KPI mentions
2. Check document content has numeric metrics
3. Use clear patterns: "KPI: Name - Value"

### Document Count Shows 0
```
"document_count": 0
```

**Solution:**
1. Vector store not loaded properly
2. Run full pipeline:
   ```powershell
   python pipeline.py
   ```
3. Check config.yaml for correct paths

## Testing the Integration

### Step 1: Verify ChromaDB
```powershell
python -c "from vector_store import VectorStore; from config import get_config; vs = VectorStore(get_config()); vs.load_vectorstore(); print(vs.get_collection_stats())"
```

### Step 2: Test Data Extractor
```python
from vector_store import VectorStore
from chroma_data_extractor import ChromaDataExtractor
from config import get_config

config = get_config()
vs = VectorStore(config)
vs.load_vectorstore()

extractor = ChromaDataExtractor(vs, config)

# Test value streams
print("Value Streams:", extractor.get_value_streams())

# Test health scores
print("Health Scores:", extractor.get_health_scores())

# Test KPIs
print("KPIs:", extractor.get_kpis())
```

### Step 3: Test API Endpoints
```powershell
# Start server
python api_server.py

# In new terminal, test endpoints
Invoke-RestMethod -Uri "http://localhost:8000/api/value-streams"
Invoke-RestMethod -Uri "http://localhost:8000/api/health-scores"
Invoke-RestMethod -Uri "http://localhost:8000/api/kpis"
```

### Step 4: Test Frontend
```powershell
# Start frontend
cd UI
npm start

# Open http://localhost:3000
# Check Dashboard for value streams
# Check data loads correctly
```

## Benefits of ChromaDB Integration

✅ **Real-time Data**: Always shows latest ingested documents  
✅ **No File Management**: No need to generate/update parquet files  
✅ **Dynamic Analysis**: Health scores calculated on-demand  
✅ **Automatic Discovery**: Value streams extracted automatically  
✅ **Metadata Filtering**: Query by category, date, document type  
✅ **Scalable**: Handles large document collections efficiently  
✅ **RAG Integration**: Same data source for both UI and chat  

## Next Steps

1. ✅ Ingest your ERP documents: `python data_ingestion.py`
2. ✅ Start backend: `python api_server.py`
3. ✅ Verify endpoints return data
4. ✅ Start frontend: `cd UI && npm start`
5. ✅ Test complete integration

No more sample data needed - everything comes from your real documents in ChromaDB!
