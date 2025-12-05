    # ERP Modernization Health Check System

    A comprehensive, production-grade RAG-based system for analyzing ERP modernization readiness using **open-source AI tools**. This system follows a structured architecture to assess pain points, process efficiency, benchmarks, and risks in enterprise systems.

    > **📚 Quick Navigation:**  
    > • [📖 Documentation Index](DOCUMENTATION_INDEX.md) - All documentation  
    > • [🏗️ Architecture](ARCHITECTURE_CURRENT.md) - Complete system architecture  
    > • [🚀 Quick Reference](QUICK_REFERENCE.md) - Quick start commands & URLs  
    > • [⚡ Quickstart Guide](QUICKSTART.md) - Fast setup

    ## 🌟 Features

    ### Core Capabilities
    - **📊 Data Ingestion & Harmonization**: Multi-format document processing (PDF, DOCX, XLSX, CSV, etc.) with automatic categorization
    - **🔍 Process Mining & Discovery**: Analyzes process workflows, identifies variants and bottlenecks
    - **💭 Sentiment & Pain Point Analysis**: NLP-based sentiment scoring using HuggingFace transformers
    - **📈 Benchmarking & Gap Analysis**: Compares KPIs against industry benchmarks
    - **⚠️ Risk & Readiness Assessment**: Evaluates modernization readiness and identifies risks
    - **📉 Interactive Visualizations**: Heatmaps, dashboards, and executive reports using Plotly
    - **🔌 REST API**: FastAPI server with async job processing
    - **🧠 RAG Knowledge Base**: ChromaDB vector store with semantic search

    ### Technology Stack (100% Open Source)
    - **LLM**: HuggingFace Transformers (Mistral, Llama, etc.)
    - **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
    - **Vector Store**: ChromaDB
    - **NLP**: TextBlob, spaCy, NLTK
    - **API Framework**: FastAPI
    - **Visualization**: Plotly, Matplotlib, Seaborn
    - **Orchestration**: LangChain

    ## 🏗️ Architecture

    The system follows a modern RAG architecture with ChromaDB integration:

    ```
    User Input → Data Ingestion → Process Mining → Sentiment Analysis
                    ↓                    ↓                ↓
            Vector Store         Benchmarking      Risk Assessment
                    ↓                    ↓                ↓
            RAG System  →  Visualization & Reporting  →  Executive Summary
    ```

    **📖 Detailed Architecture Documentation:**
    - **[ARCHITECTURE_CURRENT.md](ARCHITECTURE_CURRENT.md)** - Complete up-to-date system architecture
    - **[ARCHITECTURE_CHROMADB.md](ARCHITECTURE_CHROMADB.md)** - ChromaDB integration patterns
    - **[RAG_INTEGRATION_SUMMARY.md](RAG_INTEGRATION_SUMMARY.md)** - RAG system details

    ## 📦 Installation

    ### Prerequisites
    - Python 3.9+
    - 8GB+ RAM (16GB recommended for large models)
    - Git

    ### Quick Start

    1. **Clone the repository** (or use the existing directory):
    ```powershell
    cd c:\rag-project
    ```

    2. **Create and activate virtual environment**:
    ```powershell
    python -m venv env
    .\env\Scripts\Activate.ps1
    ```

    3. **Install dependencies**:
    ```powershell
    pip install -r requirements.txt
    ```

    4. **Download spaCy model** (optional, for advanced NLP):
    ```powershell
    python -m spacy download en_core_web_sm
    ```

    5. **Create configuration file**:
    ```powershell
    # Copy and customize the example config
    Copy-Item config_example.yaml config.yaml
    ```

    ## 🚀 Usage

    ### 1. Configuration

    Edit `config.yaml` or use environment variables:

    ```yaml
    model:
    llm_provider: huggingface
    llm_model: mistralai/Mistral-7B-Instruct-v0.2
    embedding_model: sentence-transformers/all-MiniLM-L6-v2
    llm_device: cpu  # or cuda for GPU

    vector_store:
    persist_directory: ./data/chromadb
    collection_name: erp_modernization
    
    analysis:
    enable_sentiment: true
    enable_process_mining: true
    enable_benchmarking: true
    ```

### 2. Prepare Input Data

Place your ERP documents in `./data/input/`:
- ERP usage reports (PDF, DOCX)
- Pain point feedback (TXT, CSV)
- Audit reports (PDF, XLSX)
- Process maps (DOCX, CSV)
- KPI benchmarks (XLSX, CSV)

**Important**: The system now fetches data **directly from ChromaDB** instead of sample files. All value streams, health scores, and KPIs are extracted from your ingested documents. See [CHROMADB_INTEGRATION.md](CHROMADB_INTEGRATION.md) for details.

### 3. Ingest Documents

Before using the API, ingest your documents into ChromaDB:

```powershell
# Run data ingestion to create vector store
python data_ingestion.py

# OR run the full pipeline
python pipeline.py
```

This creates the ChromaDB vector store that the API endpoints query for real-time data.

### 4. Run Analysis    #### Option A: Python Script
    ```python
    from pipeline import run_health_check

    # Run complete analysis
    results = run_health_check(
        input_directory="./data/input",
        output_directory="./data/output"
    )

    print(results['summary'])
    ```

    #### Option B: API Server
    ```powershell
    # Start the server
    python api_server.py

    # Or with custom settings
    python api_server.py --host 0.0.0.0 --port 8000
    ```

    Then use the REST API:
    ```bash
    # Start analysis
    curl -X POST "http://localhost:8000/api/v1/analyze" \
    -H "Content-Type: application/json" \
    -d '{"input_directory": "./data/input"}'

    # Check status
    curl "http://localhost:8000/api/v1/status/job_20241205_143000"

    # Get results
    curl "http://localhost:8000/api/v1/results/job_20241205_143000"

    # Query knowledge base
    curl -X POST "http://localhost:8000/api/v1/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "What are the main performance issues?", "top_k": 5}'
    
    # Get value streams from ChromaDB
    curl "http://localhost:8000/api/value-streams"
    
    # Get health scores from ChromaDB
    curl "http://localhost:8000/api/health-scores"
    
    # Get KPIs from ChromaDB
    curl "http://localhost:8000/api/kpis?vs_code=O2C"
    ```

### 5. Start React UI (Optional)

The system includes a React-based web UI:

```powershell
cd UI
npm install
npm start
```

Open http://localhost:3000 to access:
- 📊 Dashboard with value stream health scores
- 💬 AI Chat for querying your documents
- 📁 Knowledge Base management
- 📈 Reports and visualizations
- 🔍 Insights and analysis jobs

### 6. View Results    Results are generated in `./data/output/`:
    - `executive_report.html` - Comprehensive executive summary
    - `pain_point_heatmap.html` - Pain point severity visualization
    - `risk_heatmap.html` - Risk assessment heatmap
    - `sentiment_dashboard.html` - Sentiment analysis dashboard
    - `benchmark_dashboard.html` - KPI gap analysis
    - `readiness_gauge.html` - Modernization readiness score
    - `full_report.json` - Complete JSON export

    ## 📊 Sample Output

    ### Executive Summary
    ```
    ================================================================================
    ERP MODERNIZATION HEALTH CHECK - SUMMARY REPORT
    ================================================================================

    DATA INGESTION:
    Total Files Processed: 45
    Successful: 43
    Failed: 2

    SENTIMENT ANALYSIS:
    Average Sentiment: -0.234
    Negative Ratio: 45.2%
    Pain Points Identified: 87

    BENCHMARKING:
    Gaps Identified: 12
    High Priority Gaps: 5

    RISK ASSESSMENT:
    Total Risks Found: 34
    Critical Findings: 8
    Readiness Score: 62.5%
    Readiness Status: PARTIALLY_READY
    ================================================================================
    ```

    ## 🔧 Advanced Configuration

    ### Using GPU Acceleration
    ```yaml
    model:
    llm_device: cuda
    embedding_device: cuda
    load_in_8bit: true  # For memory optimization
    ```

    ### Custom Embedding Models
    ```yaml
    model:
    embedding_model: BAAI/bge-large-en-v1.5  # Better quality
    # Or for multilingual:
    embedding_model: sentence-transformers/paraphrase-multilingual-mpnet-base-v2
    ```

    ### Benchmarking Thresholds
    ```python
    # In benchmarking.py, customize INDUSTRY_BENCHMARKS:
    INDUSTRY_BENCHMARKS = {
        "process_cycle_time": {"optimal": 24, "acceptable": 48, "poor": 72},
        "automation_rate": {"optimal": 0.80, "acceptable": 0.60, "poor": 0.40},
        # Add your own KPIs...
    }
    ```

    ## 🧪 Testing

    Run the test suite:
    ```powershell
    pytest tests/ -v
    ```

    ## 📚 API Documentation

    Once the server is running, visit:
    - Swagger UI: `http://localhost:8000/docs`
    - ReDoc: `http://localhost:8000/redoc`

    ### Key Endpoints

    | Endpoint | Method | Description |
    |----------|--------|-------------|
    | `/api/v1/analyze` | POST | Start new analysis job |
    | `/api/v1/status/{job_id}` | GET | Check job status |
    | `/api/v1/results/{job_id}` | GET | Get analysis results |
    | `/api/v1/query` | POST | Query knowledge base |
    | `/api/v1/reports` | GET | List generated reports |
    | `/api/v1/upload` | POST | Upload documents |

    ## 🐛 Troubleshooting

    ### Issue: Out of Memory
    ```yaml
    # Use smaller models or quantization
    model:
    llm_model: microsoft/phi-2  # Smaller model
    load_in_8bit: true
    embedding_model: sentence-transformers/all-MiniLM-L6-v2  # Lightweight
    ```

    ### Issue: Slow Performance
    - Use GPU if available
    - Reduce `chunk_size` in config
    - Limit `top_k` for searches
    - Use lighter models

    ### Issue: Import Errors
    ```powershell
    # Reinstall dependencies
    pip install -r requirements.txt --upgrade
    ```

    ## 📁 Project Structure

    ```
    rag-project/
    ├── config.py                 # Configuration management
    ├── data_ingestion.py         # Document ingestion & harmonization
    ├── process_mining.py         # Process analysis engine
    ├── sentiment_analysis.py     # Sentiment & pain point analysis
    ├── benchmarking.py           # KPI benchmarking engine
    ├── risk_assessment.py        # Risk assessment module
    ├── visualization.py          # Visualization & reporting
    ├── vector_store.py           # ChromaDB vector store
    ├── text_processor.py         # Text chunking & processing
    ├── pipeline.py               # Main orchestration pipeline
    ├── api_server.py             # FastAPI server
    ├── requirements.txt          # Python dependencies
    ├── README.md                 # This file
    ├── config.yaml               # Configuration file
    │
    ├── data/
    │   ├── input/                # Input documents
    │   ├── processed/            # Processed data
    │   ├── chromadb/             # Vector store
    │   └── output/               # Generated reports
    │
    └── tests/                    # Test suite
    ```

    ## 🤝 Contributing

    Contributions are welcome! Please:
    1. Fork the repository
    2. Create a feature branch
    3. Make your changes
    4. Add tests
    5. Submit a pull request

    ## 📄 License

    MIT License - See LICENSE file for details

    ## 🙏 Acknowledgments

    - Built with [LangChain](https://github.com/langchain-ai/langchain)
    - Powered by [HuggingFace](https://huggingface.co/)
    - Vector store by [ChromaDB](https://www.trychroma.com/)
    - API framework by [FastAPI](https://fastapi.tiangolo.com/)

    ## 📞 Support

    For issues, questions, or contributions:
    - Open an issue on GitHub
    - Check the documentation
    - Review the API docs at `/docs`

    ---

    **Built for enterprise-grade ERP modernization assessments** 🚀
