# ChromaDB Integration - Quick Summary

## What Changed?

**Before**: API endpoints loaded data from static parquet files (`health_scores.parquet`, `kpi_targets.parquet`)  
**Now**: API endpoints fetch data **directly from ChromaDB vector store** in real-time

## Why This Is Better

✅ **Single Source of Truth**: ChromaDB is used for both RAG queries AND dashboard data  
✅ **Real-time Data**: No need to generate/update separate data files  
✅ **Automatic Discovery**: Value streams extracted from document metadata  
✅ **Dynamic Analysis**: Health scores calculated on-demand from document content  
✅ **No File Management**: No parquet files to generate or maintain  
✅ **Scalable**: Handles any number of documents efficiently  

## How It Works

```
Your Documents → Data Ingestion → ChromaDB Vector Store
                                        ↓
                            ChromaDataExtractor
                                        ↓
        ┌───────────────────────────────┴────────────────────────────┐
        ↓                              ↓                             ↓
  Value Streams                 Health Scores                      KPIs
  (from metadata)          (analyzed from content)      (extracted via patterns)
        ↓                              ↓                             ↓
                            API Endpoints
                                        ↓
                              React Frontend
```

## Quick Start

### 1. Ingest Your Documents
```powershell
cd c:\rag-project
.\env\Scripts\activate

# Ingest documents into ChromaDB
python data_ingestion.py
```

### 2. Start Backend
```powershell
# API will auto-load ChromaDB on startup
python api_server.py
```

**Look for this in logs:**
```
INFO: ChromaDB data extractor initialized with 127 documents
INFO: API Server ready!
```

### 3. Test Endpoints
```powershell
# Get value streams (from ChromaDB metadata)
Invoke-RestMethod -Uri "http://localhost:8000/api/value-streams"

# Get health scores (calculated from documents)
Invoke-RestMethod -Uri "http://localhost:8000/api/health-scores"

# Get KPIs (extracted from content)
Invoke-RestMethod -Uri "http://localhost:8000/api/kpis"
```

### 4. Start Frontend
```powershell
cd UI
npm start
```

Open http://localhost:3000 - Dashboard will show data from ChromaDB!

## Data Extraction Details

### Value Streams
- Extracted from `metadata['value_stream']`, `metadata['vs_code']`, or `metadata['category']`
- Falls back to filename pattern matching (e.g., "O2C_Report.pdf" → "O2C")
- Generates friendly names ("O2C" → "Order to Cash")

### Health Scores
Calculated by analyzing documents per value stream:
- **Document Count**: More docs = better coverage
- **Issues Found**: Mentions of "problem", "error", "bug"
- **Pain Points**: Mentions of "bottleneck", "challenge", "risk"
- **RAG Status**: Green/Yellow/Amber/Red based on score

Formula:
```
process_health = base_score - issue_penalty
system_health = base_score - (issue_penalty * 1.2)
readiness_score = (process_health + system_health) / 2
```

### KPIs
Extracted using pattern matching:
- "Order Fulfillment Rate: 85%" → KPI extracted
- "KPI: Processing Time - 3.5 days" → KPI extracted
- "Target: Customer Satisfaction - 92%" → KPI extracted

## Files Modified

### New Files Created:
1. **`chroma_data_extractor.py`** - Extracts structured data from ChromaDB
2. **`CHROMADB_INTEGRATION.md`** - Detailed integration guide
3. **`CHROMADB_SUMMARY.md`** - This quick summary

### Files Modified:
1. **`api_server.py`** - Updated to use ChromaDataExtractor instead of parquet files
   - Added `data_extractor` global variable
   - Modified `startup_event()` to initialize extractor
   - Updated 5 endpoints: `/api/value-streams`, `/api/health-scores`, `/api/health-scores/{vs_code}`, `/api/value-stream/{vs_code}/analysis`, `/api/kpis`
   - Updated `/api/v1/statistics` to show ChromaDB document count

2. **`README.md`** - Added note about ChromaDB integration

### Files No Longer Needed:
- ~~`generate_sample_data.py`~~ - Not needed anymore (but kept for reference)
- ~~`health_scores.parquet`~~ - Data now from ChromaDB
- ~~`kpi_targets.parquet`~~ - Data now from ChromaDB

## Troubleshooting

### "Data not available" Error
**Cause**: Vector store not loaded  
**Solution**: Run `python data_ingestion.py` first

### No Value Streams Found
**Cause**: Documents missing value stream metadata  
**Solution**: Organize files by folder (O2C/, P2P/, etc.) or add metadata during ingestion

### Health Scores All the Same
**Cause**: Not enough document variety  
**Solution**: Add more diverse documents per value stream

### No KPIs Extracted
**Cause**: Documents don't contain numeric metrics  
**Solution**: Add performance reports, KPI dashboards, or target definitions

## Testing

```powershell
# 1. Test data extraction directly
python -c "from vector_store import VectorStore; from chroma_data_extractor import ChromaDataExtractor; from config import get_config; vs = VectorStore(get_config()); vs.load_vectorstore(); ext = ChromaDataExtractor(vs); print(ext.get_value_streams())"

# 2. Test API endpoints
python api_server.py
# In new terminal:
Invoke-RestMethod -Uri "http://localhost:8000/api/value-streams"

# 3. Test frontend
cd UI
npm start
# Open http://localhost:3000
```

## Benefits

| Aspect | Before (Parquet Files) | After (ChromaDB) |
|--------|----------------------|------------------|
| **Data Source** | Static files | Real-time ChromaDB |
| **Updates** | Manual regeneration | Automatic from documents |
| **Value Streams** | Hardcoded in files | Auto-discovered |
| **Health Scores** | Pre-calculated | Dynamic calculation |
| **KPIs** | Manually added | Auto-extracted |
| **Maintenance** | High (file management) | Low (automatic) |
| **Scalability** | Limited | High |
| **Integration** | Separate from RAG | Unified with RAG |

## Next Steps

1. ✅ **Ingest documents**: `python data_ingestion.py`
2. ✅ **Start backend**: `python api_server.py`
3. ✅ **Start frontend**: `cd UI && npm start`
4. ✅ **Test integration**: Open http://localhost:3000
5. ✅ **Add more documents**: Drop files in `./data/input/` and re-run ingestion

## Documentation

- **Detailed Guide**: [CHROMADB_INTEGRATION.md](CHROMADB_INTEGRATION.md)
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **Integration Summary**: [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)
- **New APIs Guide**: [NEW_APIS_GUIDE.md](NEW_APIS_GUIDE.md)

---

**No more sample data needed - everything comes from your real documents!** 🎉
