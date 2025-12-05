# Deployment Guide

## Option 1: Local Development

### Windows (PowerShell)
```powershell
# Clone/Navigate to project
cd c:\rag-project

# Create virtual environment
python -m venv env
.\env\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create sample data
python create_sample_data.py

# Run analysis
python run_analysis.py -i data/input/samples

# Or start API server
python api_server.py
```

### Linux/Mac
```bash
# Navigate to project
cd /path/to/rag-project

# Create virtual environment
python3 -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create sample data
python create_sample_data.py

# Run analysis
python run_analysis.py -i data/input/samples

# Or start API server
python api_server.py
```

## Option 2: Docker

### Build and Run
```bash
# Build image
docker build -t erp-health-check .

# Run container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config.yaml:/app/config.yaml \
  --name erp-health-check \
  erp-health-check

# View logs
docker logs -f erp-health-check

# Stop container
docker stop erp-health-check
```

### Using Docker Compose
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Option 3: Cloud Deployment

### Azure Container Instances

1. **Build and push image**:
```bash
# Login to Azure
az login

# Create container registry
az acr create --resource-group myResourceGroup \
  --name myregistry --sku Basic

# Build and push
az acr build --registry myregistry \
  --image erp-health-check:v1 .
```

2. **Deploy**:
```bash
az container create \
  --resource-group myResourceGroup \
  --name erp-health-check \
  --image myregistry.azurecr.io/erp-health-check:v1 \
  --cpu 2 --memory 4 \
  --ports 8000 \
  --dns-name-label erp-health-check \
  --environment-variables \
    LOG_LEVEL=INFO
```

### AWS ECS

1. **Create ECR repository**:
```bash
aws ecr create-repository --repository-name erp-health-check
```

2. **Build and push**:
```bash
# Get login credentials
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t erp-health-check .
docker tag erp-health-check:latest \
  123456789.dkr.ecr.us-east-1.amazonaws.com/erp-health-check:latest

# Push
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/erp-health-check:latest
```

3. **Create ECS task and service** (use AWS Console or CLI)

### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/erp-health-check

# Deploy to Cloud Run
gcloud run deploy erp-health-check \
  --image gcr.io/PROJECT-ID/erp-health-check \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2
```

## Option 4: Kubernetes

### Create Kubernetes manifests

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: erp-health-check
spec:
  replicas: 2
  selector:
    matchLabels:
      app: erp-health-check
  template:
    metadata:
      labels:
        app: erp-health-check
    spec:
      containers:
      - name: erp-health-check
        image: your-registry/erp-health-check:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: erp-health-check-pvc
```

**service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: erp-health-check
spec:
  selector:
    app: erp-health-check
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy:
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Production Considerations

### Performance Optimization

1. **Use GPU for faster inference**:
```yaml
model:
  llm_device: cuda
  embedding_device: cuda
```

2. **Enable quantization for memory efficiency**:
```yaml
model:
  load_in_8bit: true
```

3. **Increase workers for API**:
```yaml
api:
  workers: 4
```

### Security

1. **Enable authentication** (add to api_server.py):
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.get("/api/v1/protected")
async def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Verify token
    pass
```

2. **Use HTTPS** with reverse proxy (nginx, traefik)

3. **Limit CORS origins**:
```yaml
api:
  cors_origins:
    - "https://yourdomain.com"
```

### Monitoring

1. **Add health check endpoints**
2. **Integrate with monitoring tools** (Prometheus, Grafana)
3. **Set up logging** (ELK stack, CloudWatch)

### Scaling

1. **Horizontal scaling**: Increase replicas in Kubernetes
2. **Caching**: Add Redis for caching results
3. **Load balancing**: Use nginx or cloud load balancer
4. **Database**: Move to PostgreSQL for job tracking

## Environment Variables

Required for production:
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Model Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LLM_DEVICE=cuda  # or cpu

# Directories
INPUT_DIR=/app/data/input
OUTPUT_DIR=/app/data/output

# Logging
LOG_LEVEL=INFO
```

## Backup Strategy

1. **Data backup**:
```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Upload to cloud storage
aws s3 cp backup-*.tar.gz s3://your-bucket/backups/
```

2. **Vector store backup**:
```bash
# Backup ChromaDB
tar -czf chromadb-backup-$(date +%Y%m%d).tar.gz data/chromadb/
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs erp-health-check

# Check resource limits
docker stats erp-health-check
```

### Out of memory
- Reduce model size
- Enable quantization
- Increase container memory limits

### Slow performance
- Use GPU
- Reduce chunk_size
- Limit concurrent requests

## Support & Maintenance

- **Monitor logs** regularly
- **Update dependencies** quarterly
- **Backup data** weekly
- **Review security** monthly
- **Update models** as needed

For issues: Check logs first, then review documentation
