# New Backend APIs - ChromaDB Integration Guide

## Overview
Added 5 new API endpoints that fetch data **directly from ChromaDB vector store** instead of static files. All value streams, health scores, and KPIs are extracted from your ingested documents in real-time.

## 🎯 Key Change: No More Sample Data!

**Before**: Endpoints loaded from parquet files (`health_scores.parquet`, `kpi_targets.parquet`)  
**Now**: Endpoints query ChromaDB directly - data comes from your actual documents!

## Setup Instructions

### Step 1: Ingest Your Documents

Instead of generating sample data, ingest your real ERP documents:

```powershell
cd c:\rag-project
.\env\Scripts\activate

# Ingest documents into ChromaDB
python data_ingestion.py

# OR run full pipeline
python pipeline.py
```

This creates the ChromaDB vector store in `./chroma_db/` (or your configured path).

### Step 2: Verify Vector Store

```powershell
# Test the integration
python test_chromadb_integration.py
```

Expected output:
```
============================================================
ChromaDB Integration Test
============================================================

1. Loading configuration...
   ✓ Config loaded
   - Vector store: ./chroma_db
   - Collection: erp_docs

2. Loading vector store...
   ✓ Vector store loaded
   - Documents: 127

3. Initializing data extractor...
   ✓ Data extractor initialized

4. Testing value streams extraction...
   ✓ Found 3 value streams:
     - O2C: Order to Cash
     - P2P: Procure to Pay
     - R2R: Record to Report

5. Testing health scores calculation...
   ✓ Calculated health scores for 3 value streams
   ...

✅ All tests passed! Ready to start API server.
```

### 1. Get Value Streams
```
GET /api/value-streams
```
Returns all available value streams with their codes and names.

**Response:**
```json
{
  "value_streams": [
    {"code": "O2C", "name": "Order to Cash"},
    {"code": "P2P", "name": "Procure to Pay"},
    ...
  ]
}
```

### 2. Get All Health Scores
```
GET /api/health-scores
```
Returns health scores for all value streams.

**Response:**
```json
[
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
  },
  ...
]
```

### 3. Get Health Score by Value Stream
```
GET /api/health-scores/{vs_code}
```
Returns health score for a specific value stream.

**Example:** `GET /api/health-scores/O2C`

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

### 4. Get Value Stream Analysis
```
GET /api/value-stream/{vs_code}/analysis
```
Returns detailed analysis including health scores and KPIs for a specific value stream.

**Example:** `GET /api/value-stream/O2C/analysis`

**Response:**
```json
{
  "vs_code": "O2C",
  "analysis": {
    "vs_code": "O2C",
    "status": "available",
    "timestamp": "2025-12-06T10:30:00",
    "health_scores": {
      "vs_code": "O2C",
      "process_health": 85.5,
      ...
    },
    "kpis": [
      {
        "vs_code": "O2C",
        "kpi_name": "Order Fulfillment Rate",
        "current_value": "82.5%",
        "target_value": "95.0%",
        ...
      },
      ...
    ]
  }
}
```

### 5. Get KPIs
```
GET /api/kpis?vs_code={vs_code}
```
Returns KPIs, optionally filtered by value stream.

**Examples:**
- All KPIs: `GET /api/kpis`
- Filtered: `GET /api/kpis?vs_code=O2C`

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
      "target_direction": "higher",
      "current_numeric": 82.5,
      "target_numeric": 95.0
    },
    ...
  ]
}
```

## Setup Instructions

### Step 1: Generate Sample Data (First Time Only)

If you don't have actual health scores and KPI data files, generate sample data:

```powershell
cd c:\rag-project
.\env\Scripts\activate
python generate_sample_data.py
```

This creates:
- `./data/output/health_scores.parquet` - Sample health scores
- `./data/input/kpi_targets.parquet` - Sample KPI data

### Step 2: Start the Backend Server

```powershell
cd c:\rag-project
.\env\Scripts\activate
python api_server.py
```

The server will:
1. Start on http://localhost:8000
2. Auto-load health scores if available
3. Auto-load KPI data if available
4. Log what data was loaded

### Step 3: Verify Endpoints

Test the new endpoints:

```powershell
# Get value streams
Invoke-RestMethod -Uri "http://localhost:8000/api/value-streams"

# Get all health scores
Invoke-RestMethod -Uri "http://localhost:8000/api/health-scores"

# Get specific health score
Invoke-RestMethod -Uri "http://localhost:8000/api/health-scores/O2C"

# Get value stream analysis
Invoke-RestMethod -Uri "http://localhost:8000/api/value-stream/O2C/analysis"

# Get KPIs
Invoke-RestMethod -Uri "http://localhost:8000/api/kpis?vs_code=O2C"
```

## Frontend Integration

The frontend already has these API calls implemented in `src/services/api.ts`:
- `fetchValueStreams()` → `/api/value-streams`
- `fetchHealthScores()` → `/api/health-scores` or `/api/health-scores/{vs_code}`
- `fetchKPIs()` → `/api/kpis?vs_code={vs_code}`

## Data Files Location

### Required Files:
1. **Health Scores**: `./data/output/health_scores.parquet`
   - Generated by running analysis
   - Or use sample data generator

2. **KPI Targets**: `./data/input/kpi_targets.parquet`
   - Should be provided or use sample data generator

### Data Schema:

**health_scores.parquet columns:**
- vs_code (str)
- process_health (float)
- system_health (float)
- readiness_score (float)
- value_at_stake_usd (int)
- rag_status (str: "Red", "Amber", "Yellow", "Green")
- kpi_count (int)
- finding_count (int)
- painpoint_count (int)

**kpi_targets.parquet columns:**
- vs_code (str)
- kpi_name (str)
- current_value (str)
- target_value (str)
- definition (str)
- target_direction (str: "higher" or "lower")
- current_numeric (float)
- target_numeric (float)

## Error Handling

### 404 Errors
If endpoints return 404:
1. Check if data files exist
2. Generate sample data: `python generate_sample_data.py`
3. Restart server

### 503 Errors
If "Pipeline not initialized":
1. Check server logs
2. Ensure config.yaml is correct
3. Restart server

## Testing the Frontend

After starting both backend and frontend:

1. **Dashboard Page** - Should show:
   - Value stream selector populated
   - Health scores for selected value stream
   - System statistics

2. **Test Flow:**
   ```
   1. Start backend: python api_server.py
   2. Start frontend: cd UI && npm start
   3. Open http://localhost:3000
   4. Select different value streams from dropdown
   5. Verify data updates correctly
   ```

## API Response Codes

- `200` - Success
- `404` - Data not found (run sample data generator)
- `500` - Server error (check logs)
- `503` - Pipeline not initialized (restart server)

## Troubleshooting

### No Value Streams Showing
```powershell
# Check if health scores loaded
curl http://localhost:8000/api/value-streams

# If empty list, generate sample data
python generate_sample_data.py

# Restart server
python api_server.py
```

### Health Scores Not Available
```powershell
# Generate sample data
python generate_sample_data.py

# Or run actual analysis
# Then restart server
```

### KPIs Not Loading
```powershell
# Check if file exists
Test-Path ./data/input/kpi_targets.parquet

# Generate if missing
python generate_sample_data.py
```

## Production Deployment

For production, replace sample data with actual data:

1. Run full ERP analysis to generate health_scores.parquet
2. Provide actual KPI targets in kpi_targets.parquet
3. Update config.yaml with correct paths
4. Restart server

## Next Steps

1. Generate sample data: `python generate_sample_data.py`
2. Start backend: `python api_server.py`
3. Start frontend: `cd UI && npm start`
4. Test all endpoints
5. Replace with actual data when available
