"""
Data Ingestion & Harmonization Module for ERP Modernization Health Check.
Handles loading, processing, and labeling of various data sources.
"""
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime
from loguru import logger
import pandas as pd
from pypdf import PdfReader
from docx import Document as DocxDocument
import openpyxl

from config import Config, get_config
from langchain.schema import Document


class DataIngestionPipeline:
    """Main data ingestion and harmonization pipeline."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the data ingestion pipeline."""
        self.config = config or get_config()
        self.supported_formats = self.config.data_ingestion.supported_formats
        
        # Statistics tracking
        self.ingestion_stats = {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "by_category": {},
            "by_format": {}
        }
    
    def ingest_directory(self, directory: Optional[str] = None) -> List[Document]:
        """
        Ingest all supported files from a directory.
        
        Args:
            directory: Path to directory (uses config default if None)
            
        Returns:
            List of LangChain Document objects with metadata
        """
        input_dir = Path(directory or self.config.data_ingestion.input_directory)
        
        if not input_dir.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")
        
        logger.info(f"Starting ingestion from: {input_dir}")
        
        documents = []
        
        # Process all supported file types
        for file_path in input_dir.rglob("*"):
            if file_path.is_file() and self._is_supported_format(file_path):
                try:
                    docs = self.ingest_file(str(file_path))
                    documents.extend(docs)
                    self.ingestion_stats["successful"] += 1
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
                    self.ingestion_stats["failed"] += 1
                
                self.ingestion_stats["total_files"] += 1
        
        logger.info(f"Ingestion complete. Processed {len(documents)} document chunks from {self.ingestion_stats['total_files']} files")
        
        return documents
    
    def ingest_file(self, file_path: str) -> List[Document]:
        """
        Ingest a single file and return document chunks with metadata.
        
        Args:
            file_path: Path to file
            
        Returns:
            List of Document objects
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Processing file: {path.name}")
        
        # Extract content based on file type
        content = self._extract_content(path)
        
        if not content or not content.strip():
            logger.warning(f"No content extracted from {path.name}")
            return []
        
        # Create base metadata
        metadata = self._create_metadata(path, content)
        
        # Auto-label if enabled
        if self.config.data_ingestion.enable_auto_labeling:
            metadata["category"] = self._auto_categorize(path, content)
            metadata["labels"] = self._extract_labels(content, metadata["category"])
        
        # Update statistics
        category = metadata.get("category", "unknown")
        self.ingestion_stats["by_category"][category] = self.ingestion_stats["by_category"].get(category, 0) + 1
        
        file_format = path.suffix.lower().lstrip('.')
        self.ingestion_stats["by_format"][file_format] = self.ingestion_stats["by_format"].get(file_format, 0) + 1
        
        # Create document
        document = Document(
            page_content=content,
            metadata=metadata
        )
        
        return [document]
    
    def _extract_content(self, file_path: Path) -> str:
        """Extract text content from various file formats."""
        suffix = file_path.suffix.lower()
        
        try:
            if suffix == '.pdf':
                return self._extract_pdf(file_path)
            elif suffix == '.docx':
                return self._extract_docx(file_path)
            elif suffix == '.xlsx':
                return self._extract_excel(file_path)
            elif suffix == '.csv':
                return self._extract_csv(file_path)
            elif suffix == '.txt':
                return self._extract_text(file_path)
            elif suffix == '.json':
                return self._extract_json(file_path)
            elif suffix == '.pptx':
                return self._extract_pptx(file_path)
            else:
                logger.warning(f"Unsupported format: {suffix}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting content from {file_path.name}: {e}")
            return ""
    
    def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from PDF."""
        reader = PdfReader(str(file_path))
        text_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    def _extract_docx(self, file_path: Path) -> str:
        """Extract text from DOCX."""
        doc = DocxDocument(str(file_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        
        # Also extract from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        paragraphs.append(cell.text)
        
        return "\n\n".join(paragraphs)
    
    def _extract_excel(self, file_path: Path) -> str:
        """Extract text from Excel."""
        df = pd.read_excel(file_path, sheet_name=None)  # Read all sheets
        
        text_parts = []
        for sheet_name, sheet_df in df.items():
            text_parts.append(f"Sheet: {sheet_name}")
            text_parts.append(sheet_df.to_string(index=False))
            text_parts.append("")
        
        return "\n".join(text_parts)
    
    def _extract_csv(self, file_path: Path) -> str:
        """Extract text from CSV."""
        df = pd.read_csv(file_path)
        return df.to_string(index=False)
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text from plain text file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _extract_json(self, file_path: Path) -> str:
        """Extract text from JSON."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    
    def _extract_pptx(self, file_path: Path) -> str:
        """Extract text from PowerPoint."""
        try:
            from pptx import Presentation
            prs = Presentation(str(file_path))
            
            text_parts = []
            for slide_num, slide in enumerate(prs.slides, 1):
                text_parts.append(f"Slide {slide_num}:")
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        text_parts.append(shape.text)
                text_parts.append("")
            
            return "\n".join(text_parts)
        except Exception as e:
            logger.warning(f"Could not extract PPTX content: {e}")
            return ""
    
    def _create_metadata(self, file_path: Path, content: str) -> Dict:
        """Create metadata for a document."""
        return {
            "source": str(file_path),
            "filename": file_path.name,
            "file_type": file_path.suffix.lower().lstrip('.'),
            "file_size": file_path.stat().st_size,
            "ingestion_timestamp": datetime.now().isoformat(),
            "content_length": len(content),
            "word_count": len(content.split())
        }
    
    def _auto_categorize(self, file_path: Path, content: str) -> str:
        """
        Automatically categorize document based on filename and content.
        
        Categories:
        - erp_exports: ERP usage data, transactions, logs
        - pain_points: User complaints, issues, feedback
        - audits: Audit reports, compliance findings
        - benchmarks: KPIs, metrics, benchmarks
        - process_maps: Process flows, workflows, BPMN
        """
        filename_lower = file_path.name.lower()
        content_lower = content.lower()
        
        category_mapping = self.config.data_ingestion.category_mapping
        
        # Score each category
        category_scores = {}
        
        for category, keywords in category_mapping.items():
            score = 0
            for keyword in keywords:
                # Check filename
                if keyword in filename_lower:
                    score += 3
                # Check content (sample first 2000 chars for performance)
                if keyword in content_lower[:2000]:
                    score += 1
            
            category_scores[category] = score
        
        # Return category with highest score, or "general" if no match
        if not category_scores or max(category_scores.values()) == 0:
            return "general"
        
        return max(category_scores.items(), key=lambda x: x[1])[0]
    
    def _extract_labels(self, content: str, category: str) -> List[str]:
        """Extract relevant labels/tags from content."""
        labels = [category]
        
        # Simple keyword extraction (can be enhanced with NLP)
        content_lower = content.lower()
        
        # Common ERP-related labels
        label_keywords = {
            "sap": ["sap", "s/4hana"],
            "oracle": ["oracle", "peoplesoft", "jd edwards"],
            "microsoft": ["dynamics", "d365"],
            "performance": ["slow", "performance", "latency", "timeout"],
            "security": ["security", "vulnerability", "breach", "compliance"],
            "integration": ["integration", "api", "interface"],
            "migration": ["migration", "modernization", "upgrade"],
            "workflow": ["workflow", "approval", "process"],
            "reporting": ["report", "analytics", "dashboard"]
        }
        
        for label, keywords in label_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                labels.append(label)
        
        return list(set(labels))  # Remove duplicates
    
    def _is_supported_format(self, file_path: Path) -> bool:
        """Check if file format is supported."""
        suffix = file_path.suffix.lower().lstrip('.')
        return suffix in self.supported_formats
    
    def get_statistics(self) -> Dict:
        """Get ingestion statistics."""
        return self.ingestion_stats
    
    def harmonize_data(self, documents: List[Document]) -> List[Document]:
        """
        Harmonize and standardize document metadata across all sources.
        
        Args:
            documents: List of documents to harmonize
            
        Returns:
            Harmonized documents
        """
        logger.info(f"Harmonizing {len(documents)} documents")
        
        harmonized = []
        
        for doc in documents:
            # Standardize metadata fields
            metadata = doc.metadata.copy()
            
            # Ensure required fields exist
            if "category" not in metadata:
                metadata["category"] = "general"
            
            if "labels" not in metadata:
                metadata["labels"] = []
            
            if "priority" not in metadata:
                metadata["priority"] = self._calculate_priority(doc)
            
            # Create harmonized document
            harmonized_doc = Document(
                page_content=doc.page_content,
                metadata=metadata
            )
            
            harmonized.append(harmonized_doc)
        
        return harmonized
    
    def _calculate_priority(self, document: Document) -> str:
        """Calculate document priority based on category and content."""
        category = document.metadata.get("category", "general")
        
        # Priority rules
        high_priority_categories = ["audits", "pain_points"]
        medium_priority_categories = ["benchmarks", "process_maps"]
        
        if category in high_priority_categories:
            return "high"
        elif category in medium_priority_categories:
            return "medium"
        else:
            return "low"
    
    def save_processed_documents(self, documents: List[Document], output_file: str = "processed_documents.json"):
        """Save processed documents to JSON."""
        output_path = Path(self.config.data_ingestion.processed_directory) / output_file
        
        serialized = []
        for doc in documents:
            serialized.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serialized, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(documents)} processed documents to {output_path}")
        return str(output_path)
