"""
FastAPI Server for ERP Modernization Health Check.
Provides REST API endpoints for all analysis functions.
"""
from typing import List, Dict, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from loguru import logger
import asyncio
from datetime import datetime
import pandas as pd
import os

from config import Config, get_config
from pipeline import ERPHealthCheckPipeline
from chroma_data_extractor import ChromaDataExtractor


# Pydantic models for API
class AnalysisRequest(BaseModel):
    """Request model for analysis."""
    input_directory: str = Field(default="./data/input", description="Input data directory")
    create_vector_store: bool = Field(default=True, description="Create vector store")


class QueryRequest(BaseModel):
    """Request model for knowledge base query."""
    query: str = Field(..., description="Query string")
    category: Optional[str] = Field(None, description="Category filter")
    top_k: int = Field(default=5, description="Number of results")
    use_rag: bool = Field(default=True, description="Use RAG for intelligent answers")


class ChatRequest(BaseModel):
    """Request model for simple chat."""
    question: str = Field(..., description="Question to ask")
    model: Optional[str] = Field(default="vector-search", description="Model to use: vector-search, openai, ollama, huggingface")
    use_llm: bool = Field(default=False, description="Use LLM for answer generation")


class BatchQueryRequest(BaseModel):
    """Request model for batch queries."""
    queries: List[str] = Field(..., description="List of questions")
    category: Optional[str] = Field(None, description="Category filter")


class AnalysisStatus(BaseModel):
    """Analysis job status."""
    job_id: str
    status: str  # pending, running, completed, failed
    progress: float  # 0-100
    message: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class HealthScoreResponse(BaseModel):
    """Health score response model."""
    vs_code: str
    process_health: float
    system_health: float
    readiness_score: float
    value_at_stake_usd: float
    rag_status: Optional[str] = None
    kpi_count: Optional[int] = None
    finding_count: Optional[int] = None
    painpoint_count: Optional[int] = None


class ValueStreamResponse(BaseModel):
    """Value stream response model."""
    code: str
    name: str


class KPIResponse(BaseModel):
    """KPI response model."""
    vs_code: str
    kpi_name: str
    current_value: str
    target_value: str
    definition: str
    target_direction: str
    current_numeric: Optional[float] = None
    target_numeric: Optional[float] = None


# Initialize FastAPI app
app = FastAPI(
    title="ERP Modernization Health Check API",
    description="REST API for ERP modernization assessment and analysis",
    version="1.0.0"
)

# Global state
config = get_config()
pipeline: Optional[ERPHealthCheckPipeline] = None
analysis_jobs: Dict[str, AnalysisStatus] = {}
analysis_results: Dict[str, Dict] = {}
data_extractor: Optional[ChromaDataExtractor] = None


# CORS middleware
if config.api.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup."""
    global pipeline, data_extractor
    logger.info("Initializing ERP Health Check Pipeline...")
    pipeline = ERPHealthCheckPipeline(config)
    
    # Try to initialize ChromaDB data extractor
    try:
        if pipeline.vector_store:
            # Try to load existing vector store
            try:
                pipeline.vector_store.load_vectorstore()
                data_extractor = ChromaDataExtractor(pipeline.vector_store, config)
                doc_count = data_extractor.get_document_count()
                logger.info(f"ChromaDB data extractor initialized with {doc_count} documents")
            except FileNotFoundError:
                logger.warning("Vector store not found. Run analysis first to create it.")
                data_extractor = None
        else:
            logger.warning("Vector store not available in pipeline")
            data_extractor = None
    except Exception as e:
        logger.error(f"Could not initialize data extractor: {e}")
        data_extractor = None
    
    logger.info("API Server ready!")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "ERP Modernization Health Check API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "value_streams": "/api/value-streams",
            "health_scores_all": "/api/health-scores",
            "health_scores_by_vs": "/api/health-scores/{vs_code}",
            "value_stream_analysis": "/api/value-stream/{vs_code}/analysis",
            "kpis": "/api/kpis?vs_code={vs_code}",
            "config": "/api/v1/config",
            "analyze": "/api/v1/analyze",
            "status": "/api/v1/status/{job_id}",
            "query": "/api/v1/query",
            "reports": "/api/v1/reports",
            "visualizations": "/api/v1/visualizations"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    pipeline_methods = []
    if pipeline is not None:
        pipeline_methods = [method for method in dir(pipeline) if not method.startswith('_')]
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "pipeline_initialized": pipeline is not None,
        "pipeline_methods": pipeline_methods if pipeline else [],
        "has_query_method": hasattr(pipeline, 'query_knowledge_base') if pipeline else False
    }


@app.get("/api/models")
async def get_available_models():
    """Get available LLM models and their configuration status."""
    models = {
        "vector-search": {
            "name": "Vector Search Only",
            "description": "Fast similarity search without LLM",
            "available": True,
            "requires_api_key": False
        },
        "openai": {
            "name": "OpenAI GPT",
            "description": "OpenAI's GPT models",
            "available": bool(os.getenv("OPENAI_API_KEY")),
            "requires_api_key": True,
            "configured_model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        },
        "ollama": {
            "name": "Ollama (Local)",
            "description": "Local LLM via Ollama",
            "available": True,  # Assumes Ollama might be available
            "requires_api_key": False,
            "configured_model": os.getenv("OLLAMA_MODEL", "llama2"),
            "url": os.getenv("OLLAMA_URL", "http://localhost:11434")
        },
        "huggingface": {
            "name": "HuggingFace Inference API",
            "description": "HuggingFace hosted models",
            "available": bool(os.getenv("HUGGINGFACE_API_KEY")),
            "requires_api_key": True,
            "configured_model": os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
        }
    }
    
    return {
        "models": models,
        "default": "vector-search",
        "recommended": "openai" if models["openai"]["available"] else "vector-search"
    }


# ============================================
# VALUE STREAM & HEALTH SCORE ENDPOINTS
# ============================================

@app.get("/api/value-streams")
async def get_value_streams():
    """Get all available value streams from ChromaDB."""
    global data_extractor
    
    try:
        if data_extractor is None:
            # Return default value streams if data extractor not initialized
            vs_names = {
                "O2C": "Order to Cash",
                "P2P": "Procure to Pay",
                "P2M": "Plan to Manufacture",
                "R2R": "Record to Report",
                "H2R": "Hire to Retire",
                "A2D": "Acquire to Decommission",
                "R2S": "Request to Service",
                "I2M": "Idea to Market",
                "DM": "Data Management"
            }
            return {
                "value_streams": [
                    {"code": k, "name": v} 
                    for k, v in vs_names.items()
                ]
            }
        
        value_streams = data_extractor.get_value_streams()
        return {"value_streams": value_streams}
        
    except Exception as e:
        logger.error(f"Error fetching value streams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health-scores", response_model=List[HealthScoreResponse])
async def get_health_scores():
    """Get health scores for all value streams from ChromaDB."""
    global data_extractor
    
    try:
        if data_extractor is None:
            raise HTTPException(
                status_code=404,
                detail="Data not available. Run analysis and create vector store first."
            )
        
        health_scores = data_extractor.get_health_scores()
        
        if not health_scores:
            raise HTTPException(
                status_code=404,
                detail="No health scores found in vector store."
            )
        
        return health_scores
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching health scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health-scores/{vs_code}", response_model=HealthScoreResponse)
async def get_health_score_by_vs(vs_code: str):
    """Get health score for a specific value stream from ChromaDB."""
    global data_extractor
    
    try:
        if data_extractor is None:
            raise HTTPException(
                status_code=404,
                detail="Data not available. Run analysis and create vector store first."
            )
        
        # Get valid value streams for better error message
        valid_streams = data_extractor.get_value_streams()
        valid_codes = [vs['code'] for vs in valid_streams]
        
        # Try exact match first
        health_scores = data_extractor.get_health_scores(vs_code=vs_code)
        
        # If not found, try case-insensitive match
        if not health_scores:
            vs_code_lower = vs_code.lower()
            health_scores = data_extractor.get_health_scores(vs_code=vs_code_lower)
        
        if not health_scores:
            raise HTTPException(
                status_code=404,
                detail=f"Health score not found for value stream '{vs_code}'. Valid value streams: {', '.join(valid_codes)}"
            )
        
        return health_scores[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching health score for {vs_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/value-stream/{vs_code}/analysis")
async def get_value_stream_analysis(vs_code: str):
    """Get detailed analysis for a specific value stream from ChromaDB."""
    global data_extractor
    
    try:
        if data_extractor is None:
            raise HTTPException(
                status_code=404,
                detail="Data not available. Run analysis and create vector store first."
            )
        
        # Try exact match first, then case-insensitive
        health_scores = data_extractor.get_health_scores(vs_code=vs_code)
        if not health_scores:
            health_scores = data_extractor.get_health_scores(vs_code=vs_code.lower())
        
        if not health_scores:
            valid_streams = data_extractor.get_value_streams()
            valid_codes = [vs['code'] for vs in valid_streams]
            raise HTTPException(
                status_code=404,
                detail=f"Value stream not found: {vs_code}. Valid value streams: {', '.join(valid_codes)}"
            )
        
        health_score = health_scores[0]
        actual_vs_code = health_score['vs_code']
        
        # Get KPIs using the actual vs_code from the health score
        kpis = data_extractor.get_kpis(vs_code=actual_vs_code)
        
        return {
            "vs_code": actual_vs_code,
            "analysis": {
                "vs_code": actual_vs_code,
                "status": "available",
                "timestamp": datetime.now().isoformat(),
                "health_scores": health_score,
                "kpis": kpis
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analysis for {vs_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kpis")
async def get_kpis(vs_code: Optional[str] = None):
    """Get KPIs from ChromaDB, optionally filtered by value stream."""
    global data_extractor
    
    try:
        if data_extractor is None:
            raise HTTPException(
                status_code=404,
                detail="Data not available. Run analysis and create vector store first."
            )
        
        # Try exact match first, then case-insensitive
        kpis = None
        if vs_code:
            kpis = data_extractor.get_kpis(vs_code=vs_code)
            if not kpis:
                kpis = data_extractor.get_kpis(vs_code=vs_code.lower())
        else:
            kpis = data_extractor.get_kpis(vs_code=None)
        
        if not kpis:
            # Get valid value streams for better error message
            valid_streams = data_extractor.get_value_streams()
            valid_codes = [vs['code'] for vs in valid_streams]
            msg = f"No KPIs found for value stream '{vs_code}'. Valid value streams: {', '.join(valid_codes)}" if vs_code else "No KPIs found."
            raise HTTPException(status_code=404, detail=msg)
        
        return {"kpis": kpis}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# LLM HELPER FUNCTIONS
# ============================================

async def _generate_with_openai(question: str, context: str) -> str:
    """Generate answer using OpenAI API."""
    try:
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        
        client = openai.OpenAI(api_key=api_key)
        
        prompt = f"""Use the following context to answer the question. If you don't know the answer based on the context, say so.

Context:
{context}

Question: {question}

Answer:"""
        
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant for ERP modernization questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI generation failed: {e}")
        raise


async def _generate_with_ollama(question: str, context: str) -> str:
    """Generate answer using Ollama local API."""
    try:
        import httpx
        
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama2")
        
        prompt = f"""Use the following context to answer the question. If you don't know the answer based on the context, say so.

Context:
{context}

Question: {question}

Answer:"""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 1000
                    }
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"Ollama API returned {response.status_code}")
            
            result = response.json()
            return result.get("response", "No response generated")
        
    except Exception as e:
        logger.error(f"Ollama generation failed: {e}")
        raise


async def _generate_with_huggingface(question: str, context: str) -> str:
    """Generate answer using HuggingFace Inference API."""
    try:
        import httpx
        
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            raise ValueError("HUGGINGFACE_API_KEY not set in environment")
        
        model = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
        
        prompt = f"""Use the following context to answer the question. If you don't know the answer based on the context, say so.

Context:
{context}

Question: {question}

Answer:"""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 1000,
                        "temperature": 0.1,
                        "return_full_text": False
                    }
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"HuggingFace API returned {response.status_code}")
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "No response generated")
            return "No response generated"
        
    except Exception as e:
        logger.error(f"HuggingFace generation failed: {e}")
        raise


# ============================================
# EXISTING ENDPOINTS CONTINUE BELOW
# ============================================

@app.get("/api/v1/config")
async def get_configuration():
    """Get current configuration."""
    return {
        "model": config.model.model_dump(),
        "vector_store": config.vector_store.model_dump(),
        "analysis": config.analysis.model_dump(),
        "visualization": config.visualization.model_dump()
    }


@app.post("/api/v1/analyze", response_model=AnalysisStatus)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new analysis job.
    
    This endpoint initiates an asynchronous analysis job and returns immediately
    with a job_id. Use the /status endpoint to check progress.
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    # Generate job ID
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create job status
    job_status = AnalysisStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message="Analysis job queued",
        started_at=datetime.now().isoformat()
    )
    
    analysis_jobs[job_id] = job_status
    
    # Start background task
    background_tasks.add_task(
        run_analysis_task,
        job_id,
        request.input_directory,
        request.create_vector_store
    )
    
    logger.info(f"Started analysis job: {job_id}")
    
    return job_status


async def run_analysis_task(
    job_id: str,
    input_directory: str,
    create_vector_store: bool
):
    """Background task to run analysis."""
    try:
        # Update status
        analysis_jobs[job_id].status = "running"
        analysis_jobs[job_id].progress = 10.0
        analysis_jobs[job_id].message = "Running analysis..."
        
        # Run analysis
        results = pipeline.run_full_analysis(
            input_directory=input_directory,
            create_vector_store=create_vector_store
        )
        
        analysis_jobs[job_id].progress = 70.0
        analysis_jobs[job_id].message = "Generating visualizations..."
        
        # Generate visualizations
        generated_files = pipeline.generate_visualizations(results)
        
        # Store results
        analysis_results[job_id] = {
            "results": results,
            "generated_files": generated_files,
            "summary": pipeline.generate_summary_report(results)
        }
        
        # Update status
        analysis_jobs[job_id].status = "completed"
        analysis_jobs[job_id].progress = 100.0
        analysis_jobs[job_id].message = "Analysis completed successfully"
        analysis_jobs[job_id].completed_at = datetime.now().isoformat()
        
        logger.info(f"Completed analysis job: {job_id}")
        
    except Exception as e:
        logger.error(f"Analysis job {job_id} failed: {e}")
        analysis_jobs[job_id].status = "failed"
        analysis_jobs[job_id].message = f"Analysis failed: {str(e)}"
        analysis_jobs[job_id].completed_at = datetime.now().isoformat()


@app.get("/api/v1/status/{job_id}", response_model=AnalysisStatus)
async def get_analysis_status(job_id: str):
    """Get status of an analysis job."""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return analysis_jobs[job_id]


@app.get("/api/v1/results/{job_id}")
async def get_analysis_results(job_id: str):
    """Get results of a completed analysis job."""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if analysis_jobs[job_id].status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job status is {analysis_jobs[job_id].status}, not completed"
        )
    
    if job_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    return analysis_results[job_id]


@app.post("/api/v1/query")
async def query_knowledge_base(request: QueryRequest):
    """Query the knowledge base using RAG or vector search."""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        result = pipeline.query_knowledge_base(
            query=request.query,
            category=request.category,
            top_k=request.top_k,
            use_rag=request.use_rag
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["message"])
        
        # Format response
        return {
            "query": request.query,
            "answer": result.get("answer", ""),
            "category": request.category,
            "sources": result.get("sources", []),
            "results_count": len(result.get("sources", [])),
            "use_rag": request.use_rag
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """Chat interface with multiple model support and comprehensive guardrails."""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    # Input validation guardrails
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if len(request.question) > 1000:
        raise HTTPException(status_code=400, detail="Question too long (max 1000 characters)")
    
    try:
        # Load vector store if not loaded
        if pipeline.vector_store.vectorstore is None:
            try:
                pipeline.vector_store.load_vectorstore()
            except Exception as ve:
                logger.error(f"Vector store not available: {ve}")
                raise HTTPException(
                    status_code=503,
                    detail="Knowledge base not initialized. Please run analysis first to create the vector store."
                )
        
        # Get relevant documents first
        try:
            docs = pipeline.vector_store.similarity_search(
                query=request.question.strip(),
                k=5
            )
        except Exception as search_error:
            logger.error(f"Vector search failed: {search_error}")
            raise HTTPException(
                status_code=500,
                detail="Failed to search knowledge base. Please try again."
            )
        
        if not docs:
            return {
                "question": request.question,
                "answer": "I couldn't find any relevant information in the knowledge base for your question.",
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "model_used": "none",
                "sources_count": 0
            }
        
        # Build context from retrieved documents
        context = "\n\n".join([doc.page_content[:800] for doc in docs[:3]])
        
        # Determine which model to use
        answer = None
        model_used = request.model
        
        if request.use_llm and request.model != "vector-search":
            # Try to use LLM for better answers
            try:
                if request.model == "openai":
                    answer = await _generate_with_openai(request.question, context)
                    model_used = "openai"
                elif request.model == "ollama":
                    answer = await _generate_with_ollama(request.question, context)
                    model_used = "ollama"
                elif request.model == "huggingface":
                    answer = await _generate_with_huggingface(request.question, context)
                    model_used = "huggingface"
                else:
                    logger.warning(f"Unknown model: {request.model}, falling back to vector search")
            except Exception as llm_error:
                logger.warning(f"LLM generation failed: {llm_error}, falling back to vector search")
        
        # Fallback to vector search results
        if answer is None:
            context_parts = []
            for i, doc in enumerate(docs[:3], 1):
                content = doc.page_content[:500]
                source = doc.metadata.get('source', 'Unknown')
                context_parts.append(f"{i}. {content}")
            
            answer = f"Based on the available documentation:\n\n" + "\n\n".join(context_parts)
            answer += f"\n\n(Retrieved {len(docs)} relevant document(s))"
            model_used = "vector-search"
        
        return {
            "question": request.question,
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "model_used": model_used,
            "sources_count": len(docs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your question. Please try again."
        )


@app.post("/api/v1/batch-query")
async def batch_query(request: BatchQueryRequest):
    """Process multiple questions in batch with comprehensive guardrails."""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    # Input validation guardrails
    if not request.queries or len(request.queries) == 0:
        raise HTTPException(status_code=400, detail="Queries list cannot be empty")
    
    if len(request.queries) > 50:
        raise HTTPException(status_code=400, detail="Too many queries (max 50 per batch)")
    
    # Validate each query
    for i, query in enumerate(request.queries):
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail=f"Query at index {i} is empty")
        if len(query) > 1000:
            raise HTTPException(status_code=400, detail=f"Query at index {i} is too long (max 1000 characters)")
    
    try:
        # Load vector store if not loaded
        if pipeline.vector_store.vectorstore is None:
            try:
                pipeline.vector_store.load_vectorstore()
            except Exception as ve:
                logger.error(f"Vector store not available: {ve}")
                raise HTTPException(
                    status_code=503,
                    detail="Knowledge base not initialized. Please run analysis first."
                )
        
        # Process queries using vector similarity search
        results = []
        for query in request.queries:
            try:
                docs = pipeline.vector_store.similarity_search(
                    query=query.strip(),
                    k=3
                )
                
                if not docs:
                    results.append({
                        "question": query,
                        "answer": "No relevant information found in the knowledge base.",
                        "error": False,
                        "sources_count": 0
                    })
                else:
                    # Create answer from retrieved documents
                    context_parts = []
                    for i, doc in enumerate(docs[:3], 1):
                        content = doc.page_content[:300]
                        context_parts.append(f"{i}. {content}")
                    
                    answer = "Based on the documentation:\\n\\n" + "\\n\\n".join(context_parts)
                    
                    results.append({
                        "question": query,
                        "answer": answer,
                        "error": False,
                        "sources_count": len(docs)
                    })
            except Exception as query_error:
                logger.error(f"Failed to process query '{query}': {query_error}")
                results.append({
                    "question": query,
                    "answer": f"Error processing query: {str(query_error)}",
                    "error": True,
                    "sources_count": 0
                })
        
        # Count successful vs failed queries
        success_count = sum(1 for r in results if not r.get('error', False))
        error_count = len(results) - success_count
        
        return {
            "queries_count": len(request.queries),
            "success_count": success_count,
            "error_count": error_count,
            "results": results,
            "timestamp": datetime.now().isoformat(),
            "status": "completed" if error_count == 0 else "partial_success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing batch queries. Please try again."
        )


@app.get("/api/v1/reports")
async def list_reports():
    """List all available reports and visualizations."""
    output_dir = Path(config.visualization.output_directory)
    
    if not output_dir.exists():
        return {"reports": [], "message": "No reports generated yet"}
    
    reports = []
    for file_path in output_dir.glob("*"):
        if file_path.is_file():
            reports.append({
                "name": file_path.name,
                "type": file_path.suffix.lstrip('.'),
                "size": file_path.stat().st_size,
                "created": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                "path": str(file_path)
            })
    
    return {"reports": reports, "count": len(reports)}


@app.get("/api/v1/visualizations/{filename}")
async def get_visualization(filename: str):
    """Download a specific visualization file."""
    file_path = Path(config.visualization.output_directory) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@app.get("/api/v1/statistics")
async def get_statistics():
    """Get overall system statistics from ChromaDB."""
    global data_extractor
    
    stats = {
        "total_jobs": len(analysis_jobs),
        "completed_jobs": sum(1 for job in analysis_jobs.values() if job.status == "completed"),
        "failed_jobs": sum(1 for job in analysis_jobs.values() if job.status == "failed"),
        "running_jobs": sum(1 for job in analysis_jobs.values() if job.status == "running")
    }
    
    # Vector store stats from data extractor
    try:
        if data_extractor:
            stats["vector_store"] = {
                "collection_name": data_extractor.vector_store.collection_name,
                "persist_directory": data_extractor.vector_store.persist_directory,
                "document_count": data_extractor.get_document_count()
            }
        elif pipeline and pipeline.vector_store:
            stats["vector_store"] = pipeline.vector_store.get_collection_stats()
    except Exception as e:
        logger.warning(f"Could not get vector store stats: {e}")
    
    return stats


@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a document for analysis."""
    try:
        # Save uploaded file
        input_dir = Path(config.data_ingestion.input_directory)
        input_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = input_dir / file.filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Uploaded file: {file.filename}")
        
        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "size": len(content),
            "path": str(file_path)
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its results."""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Remove from both dictionaries
    del analysis_jobs[job_id]
    if job_id in analysis_results:
        del analysis_results[job_id]
    
    return {"message": f"Job {job_id} deleted successfully"}


def start_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    reload: Optional[bool] = None
):
    """
    Start the FastAPI server.
    
    Args:
        host: Host address
        port: Port number
        reload: Enable auto-reload
    """
    uvicorn.run(
        "api_server:app",
        host=host or config.api.host,
        port=port or config.api.port,
        reload=reload if reload is not None else config.api.reload,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()
