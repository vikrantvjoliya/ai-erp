# Quick Start Guide

## Installation

1. **Install Dependencies**:
```powershell
pip install -r requirements.txt
```

2. **Create Sample Data**:
```powershell
python create_sample_data.py
```

3. **Run Analysis**:
```powershell
python run_analysis.py -i data/input/samples
```

## Using the API

1. **Start Server**:
```powershell
python api_server.py
```

2. **Access API Documentation**:
Open browser: http://localhost:8000/docs

3. **Run Analysis via API**:
```powershell
# Start analysis
curl -X POST "http://localhost:8000/api/v1/analyze" -H "Content-Type: application/json" -d "{\"input_directory\": \"./data/input/samples\"}"

# Check status (replace job_id with actual ID from response)
curl "http://localhost:8000/api/v1/status/job_20241205_120000"

# Get results
curl "http://localhost:8000/api/v1/results/job_20241205_120000"
```

## View Reports

After analysis, open these files in your browser:
- `data/output/executive_report.html`
- `data/output/sentiment_dashboard.html`
- `data/output/benchmark_dashboard.html`
- `data/output/pain_point_heatmap.html`
- `data/output/risk_heatmap.html`

## Query Knowledge Base

```powershell
python run_analysis.py --query "What are the main performance issues?"
```

## Troubleshooting

### Out of Memory?
Edit `config.yaml`:
```yaml
model:
  llm_model: microsoft/phi-2  # Smaller model
  load_in_8bit: true
```

### Slow Performance?
- Use GPU: set `llm_device: cuda` in config.yaml
- Reduce chunk_size: set to 500 instead of 1000
- Use lighter embedding model

### Module Not Found?
```powershell
pip install -r requirements.txt --upgrade
```

## Next Steps

1. **Add Your Own Data**: Place documents in `data/input/`
2. **Customize Config**: Edit `config.yaml`
3. **Extend Analysis**: Modify analysis modules in Python files
4. **Deploy**: Use Docker or deploy API to cloud

## Common Commands

```powershell
# Run with custom config
python run_analysis.py -i ./data/input -c ./config.yaml

# Skip vector store creation
python run_analysis.py --no-vector-store

# Query existing knowledge base
python run_analysis.py --query "List all security risks"

# Start API server on different port
python api_server.py --port 9000
```
