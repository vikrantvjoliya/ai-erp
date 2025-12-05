"""
Enhanced Configuration Management for ERP Modernization Health Check RAG System.
Supports open-source models and production-grade settings.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import yaml

load_dotenv()


class ModelConfig(BaseModel):
    """LLM and Embedding model configuration."""
    
    # Open Source LLM Options
    llm_provider: str = Field(default="huggingface", description="huggingface, ollama, or openai")
    llm_model: str = Field(default="mistralai/Mistral-7B-Instruct-v0.2", description="Model identifier")
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=2048, ge=256, le=8192)
    llm_device: str = Field(default="cpu", description="cpu, cuda, or mps")
    
    # Embedding Model Configuration
    embedding_provider: str = Field(default="huggingface", description="huggingface or openai")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_device: str = Field(default="cpu")
    
    # Model Loading Options
    load_in_8bit: bool = Field(default=False, description="Enable 8-bit quantization")
    load_in_4bit: bool = Field(default=False, description="Enable 4-bit quantization")
    trust_remote_code: bool = Field(default=False)


class VectorStoreConfig(BaseModel):
    """ChromaDB Vector Store configuration."""
    
    persist_directory: str = Field(default="./data/chromadb")
    collection_name: str = Field(default="erp_modernization")
    distance_metric: str = Field(default="cosine", description="cosine, l2, or ip")
    
    # Retrieval settings
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class ChunkingConfig(BaseModel):
    """Document chunking configuration."""
    
    chunk_size: int = Field(default=1000, ge=100, le=4000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    
    # Semantic chunking options
    use_semantic_chunking: bool = Field(default=False)
    breakpoint_threshold_amount: int = Field(default=95)


class DataIngestionConfig(BaseModel):
    """Data ingestion and harmonization settings."""
    
    input_directory: str = Field(default="./data/input")
    processed_directory: str = Field(default="./data/processed")
    
    # Supported file types
    supported_formats: list = Field(default=["pdf", "docx", "xlsx", "csv", "txt", "pptx"])
    
    # Labeling and categorization
    enable_auto_labeling: bool = Field(default=True)
    category_mapping: Dict[str, list] = Field(default={
        "erp_exports": ["usage", "transaction", "log"],
        "pain_points": ["complaint", "issue", "feedback"],
        "audits": ["audit", "compliance", "finding"],
        "benchmarks": ["benchmark", "kpi", "metric"],
        "process_maps": ["bpmn", "workflow", "process"]
    })


class AnalysisConfig(BaseModel):
    """Analysis pipeline configuration."""
    
    # Sentiment Analysis
    enable_sentiment: bool = Field(default=True)
    sentiment_model: str = Field(default="distilbert-base-uncased-finetuned-sst-2-english")
    
    # Process Mining
    enable_process_mining: bool = Field(default=True)
    min_variant_frequency: float = Field(default=0.05)
    
    # Benchmarking
    enable_benchmarking: bool = Field(default=True)
    benchmark_threshold: float = Field(default=0.85)
    
    # Risk Assessment
    risk_weights: Dict[str, float] = Field(default={
        "high": 1.0,
        "medium": 0.6,
        "low": 0.3
    })


class VisualizationConfig(BaseModel):
    """Visualization and reporting settings."""
    
    output_directory: str = Field(default="./data/output")
    
    # Heatmap settings
    heatmap_colorscale: str = Field(default="RdYlGn_r")
    heatmap_width: int = Field(default=1200)
    heatmap_height: int = Field(default=800)
    
    # Report formats
    export_formats: list = Field(default=["html", "json", "pdf"])
    
    # Dashboard settings
    enable_interactive_dashboard: bool = Field(default=True)
    dashboard_theme: str = Field(default="plotly_white")


class APIConfig(BaseModel):
    """API server configuration."""
    
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1024, le=65535)
    reload: bool = Field(default=True)
    workers: int = Field(default=1, ge=1, le=8)
    
    # CORS settings
    enable_cors: bool = Field(default=True)
    cors_origins: list = Field(default=["*"])
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=False)
    max_requests_per_minute: int = Field(default=60)


class Config:
    """Main configuration manager for the ERP Modernization Health Check system."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration from environment and optional YAML file."""
        
        # Load from YAML if provided
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
        else:
            config_data = {}
        
        # Initialize all configuration sections
        self.model = ModelConfig(**config_data.get('model', {}))
        self.vector_store = VectorStoreConfig(**config_data.get('vector_store', {}))
        self.chunking = ChunkingConfig(**config_data.get('chunking', {}))
        self.data_ingestion = DataIngestionConfig(**config_data.get('data_ingestion', {}))
        self.analysis = AnalysisConfig(**config_data.get('analysis', {}))
        self.visualization = VisualizationConfig(**config_data.get('visualization', {}))
        self.api = APIConfig(**config_data.get('api', {}))
        
        # Create necessary directories
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.vector_store.persist_directory,
            self.data_ingestion.input_directory,
            self.data_ingestion.processed_directory,
            self.visualization.output_directory,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration to dictionary."""
        return {
            'model': self.model.model_dump(),
            'vector_store': self.vector_store.model_dump(),
            'chunking': self.chunking.model_dump(),
            'data_ingestion': self.data_ingestion.model_dump(),
            'analysis': self.analysis.model_dump(),
            'visualization': self.visualization.model_dump(),
            'api': self.api.model_dump(),
        }
    
    def save(self, filepath: str):
        """Save configuration to YAML file."""
        with open(filepath, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)
    
    @classmethod
    def from_yaml(cls, filepath: str) -> 'Config':
        """Load configuration from YAML file."""
        return cls(config_file=filepath)
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        # Check if model paths are accessible
        if self.model.llm_provider == "huggingface":
            # Basic validation - actual model loading happens later
            if not self.model.llm_model:
                raise ValueError("LLM model name is required for HuggingFace provider")
        
        # Validate directories exist
        required_dirs = [
            self.vector_store.persist_directory,
            self.data_ingestion.input_directory,
        ]
        
        for directory in required_dirs:
            if not Path(directory).parent.exists():
                raise ValueError(f"Parent directory for {directory} does not exist")
        
        return True


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config(config_file: Optional[str] = None) -> Config:
    """Get or create global configuration instance."""
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config(config_file=config_file)
    
    return _config_instance


def reset_config():
    """Reset global configuration instance."""
    global _config_instance
    _config_instance = None
