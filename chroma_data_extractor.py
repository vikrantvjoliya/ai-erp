"""
Extract value streams, health scores, and KPIs from ChromaDB vector store.
Analyzes document metadata and content to derive insights.
"""
from typing import List, Dict, Optional
from pathlib import Path
from loguru import logger
from collections import defaultdict, Counter
import re

from vector_store import VectorStore
from config import Config, get_config


class ChromaDataExtractor:
    """Extract structured data from ChromaDB for API endpoints."""
    
    def __init__(self, vector_store: VectorStore, config: Optional[Config] = None):
        """
        Initialize the data extractor.
        
        Args:
            vector_store: Initialized VectorStore instance
            config: Configuration object
        """
        self.vector_store = vector_store
        self.config = config or get_config()
        self._cache = {}
        
    def get_value_streams(self) -> List[Dict[str, str]]:
        """
        Extract unique value streams from document metadata.
        
        Returns:
            List of dicts with 'code' and 'name' keys
        """
        if 'value_streams' in self._cache:
            return self._cache['value_streams']
        
        try:
            if self.vector_store.vectorstore is None:
                logger.warning("Vector store not loaded")
                return []
            
            # Get collection to access all documents
            collection = self._get_collection()
            if not collection:
                return []
            
            # Fetch all documents with metadata
            data = collection.get(include=['metadatas'])
            metadatas = data.get('metadatas', [])
            
            # Extract value streams from metadata
            value_streams_set = set()
            vs_names = {}
            
            for metadata in metadatas:
                if not metadata:
                    continue
                
                # Check various metadata fields for value stream info
                vs_code = (metadata.get('value_stream') or 
                          metadata.get('vs_code') or 
                          metadata.get('category'))
                
                vs_name = metadata.get('value_stream_name') or metadata.get('category_name')
                
                if vs_code:
                    value_streams_set.add(vs_code)
                    if vs_name:
                        vs_names[vs_code] = vs_name
            
            # If no value streams found in metadata, try to extract from content/filenames
            if not value_streams_set:
                logger.info("No value streams in metadata, attempting extraction from content")
                value_streams_set, vs_names = self._extract_from_content(metadatas)
            
            # Create value stream list with names
            value_streams = []
            for vs_code in sorted(value_streams_set):
                value_streams.append({
                    'code': vs_code,
                    'name': vs_names.get(vs_code, self._generate_vs_name(vs_code))
                })
            
            self._cache['value_streams'] = value_streams
            logger.info(f"Extracted {len(value_streams)} value streams from ChromaDB")
            return value_streams
            
        except Exception as e:
            logger.error(f"Error extracting value streams: {e}")
            return []
    
    def get_health_scores(self, vs_code: Optional[str] = None) -> List[Dict]:
        """
        Calculate health scores based on document analysis.
        
        Args:
            vs_code: Optional filter for specific value stream
            
        Returns:
            List of health score dictionaries
        """
        try:
            value_streams = self.get_value_streams()
            if not value_streams:
                return []
            
            health_scores = []
            
            for vs in value_streams:
                if vs_code and vs['code'] != vs_code:
                    continue
                
                score = self._calculate_health_score(vs['code'])
                health_scores.append(score)
            
            return health_scores if not vs_code else health_scores
            
        except Exception as e:
            logger.error(f"Error calculating health scores: {e}")
            return []
    
    def get_kpis(self, vs_code: Optional[str] = None) -> List[Dict]:
        """
        Extract KPIs from document content and metadata.
        
        Args:
            vs_code: Optional filter for specific value stream
            
        Returns:
            List of KPI dictionaries
        """
        try:
            collection = self._get_collection()
            if not collection:
                return []
            
            # Get documents with content
            data = collection.get(include=['metadatas', 'documents'])
            metadatas = data.get('metadatas', [])
            documents = data.get('documents', [])
            
            kpis = []
            
            # Search for KPI patterns in documents
            for i, (metadata, content) in enumerate(zip(metadatas, documents)):
                if not metadata or not content:
                    continue
                
                doc_vs_code = (metadata.get('value_stream') or 
                             metadata.get('vs_code') or 
                             metadata.get('category'))
                
                if vs_code and doc_vs_code != vs_code:
                    continue
                
                # Extract KPIs from content
                extracted_kpis = self._extract_kpis_from_content(content, doc_vs_code or 'Unknown')
                kpis.extend(extracted_kpis)
            
            # Deduplicate by (vs_code, kpi_name)
            unique_kpis = {}
            for kpi in kpis:
                key = (kpi['vs_code'], kpi['kpi_name'])
                if key not in unique_kpis:
                    unique_kpis[key] = kpi
            
            return list(unique_kpis.values())
            
        except Exception as e:
            logger.error(f"Error extracting KPIs: {e}")
            return []
    
    def get_document_count(self) -> int:
        """Get total number of documents in vector store."""
        try:
            stats = self.vector_store.get_collection_stats()
            count = stats.get('document_count', 0)
            return count if isinstance(count, int) else 0
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0
    
    def _get_collection(self):
        """Get ChromaDB collection object."""
        try:
            if self.vector_store.vectorstore is None:
                return None
            
            # Try different ways to access the collection
            collection = (getattr(self.vector_store.vectorstore, 'collection', None) or
                         getattr(self.vector_store.vectorstore, '_collection', None))
            
            if not collection and hasattr(self.vector_store.vectorstore, 'client'):
                client = self.vector_store.vectorstore.client
                collection = client.get_collection(self.vector_store.collection_name)
            
            return collection
        except Exception as e:
            logger.error(f"Could not access collection: {e}")
            return None
    
    def _extract_from_content(self, metadatas: List[Dict]) -> tuple:
        """Extract value streams from document content and filenames."""
        value_streams = set()
        vs_names = {}
        
        # Common value stream patterns
        vs_patterns = [
            r'\b(O2C|Order[- ]to[- ]Cash)\b',
            r'\b(P2P|Procure[- ]to[- ]Pay|Purchase[- ]to[- ]Pay)\b',
            r'\b(R2R|Record[- ]to[- ]Report)\b',
            r'\b(S2P|Source[- ]to[- ]Pay)\b',
            r'\b(PTP|Plan[- ]to[- ]Product)\b',
            r'\b(HCM|HR|Human[- ]Capital)\b',
            r'\b(SCM|Supply[- ]Chain)\b',
            r'\b(CRM|Customer[- ]Relationship)\b',
            r'\b(FIN|Finance|Financial)\b',
        ]
        
        for metadata in metadatas:
            if not metadata:
                continue
            
            # Check filename/source
            source = metadata.get('source', '') or metadata.get('file_name', '')
            
            for pattern in vs_patterns:
                match = re.search(pattern, source, re.IGNORECASE)
                if match:
                    code = self._normalize_vs_code(match.group(1))
                    value_streams.add(code)
                    vs_names[code] = self._generate_vs_name(code)
        
        # If still empty, create default categories
        if not value_streams:
            default_vs = [
                ('O2C', 'Order to Cash'),
                ('P2P', 'Procure to Pay'),
                ('R2R', 'Record to Report'),
            ]
            for code, name in default_vs:
                value_streams.add(code)
                vs_names[code] = name
        
        return value_streams, vs_names
    
    def _normalize_vs_code(self, code: str) -> str:
        """Normalize value stream code to standard format."""
        code = code.upper().strip()
        
        # Map common variations
        mappings = {
            'ORDER TO CASH': 'O2C',
            'ORDER-TO-CASH': 'O2C',
            'PROCURE TO PAY': 'P2P',
            'PROCURE-TO-PAY': 'P2P',
            'PURCHASE TO PAY': 'P2P',
            'PURCHASE-TO-PAY': 'P2P',
            'RECORD TO REPORT': 'R2R',
            'RECORD-TO-REPORT': 'R2R',
            'SOURCE TO PAY': 'S2P',
            'SOURCE-TO-PAY': 'S2P',
            'PLAN TO PRODUCT': 'PTP',
            'PLAN-TO-PRODUCT': 'PTP',
            'HUMAN CAPITAL': 'HCM',
            'HUMAN-CAPITAL': 'HCM',
            'SUPPLY CHAIN': 'SCM',
            'SUPPLY-CHAIN': 'SCM',
            'CUSTOMER RELATIONSHIP': 'CRM',
            'CUSTOMER-RELATIONSHIP': 'CRM',
        }
        
        return mappings.get(code, code)
    
    def _generate_vs_name(self, code: str) -> str:
        """Generate full name from value stream code."""
        name_map = {
            'O2C': 'Order to Cash',
            'P2P': 'Procure to Pay',
            'R2R': 'Record to Report',
            'S2P': 'Source to Pay',
            'PTP': 'Plan to Product',
            'HCM': 'Human Capital Management',
            'HR': 'Human Resources',
            'SCM': 'Supply Chain Management',
            'CRM': 'Customer Relationship Management',
            'FIN': 'Finance',
        }
        return name_map.get(code, code)
    
    def _calculate_health_score(self, vs_code: str) -> Dict:
        """
        Calculate health score for a value stream based on document analysis.
        
        Args:
            vs_code: Value stream code
            
        Returns:
            Health score dictionary
        """
        try:
            collection = self._get_collection()
            if not collection:
                return self._default_health_score(vs_code)
            
            # Get documents for this value stream
            data = collection.get(
                where={"$or": [
                    {"value_stream": vs_code},
                    {"vs_code": vs_code},
                    {"category": vs_code}
                ]},
                include=['metadatas', 'documents']
            )
            
            metadatas = data.get('metadatas', [])
            documents = data.get('documents', [])
            
            if not documents:
                # Try without filter if no documents found
                all_data = collection.get(include=['metadatas', 'documents'])
                metadatas = all_data.get('metadatas', [])
                documents = all_data.get('documents', [])
            
            # Analyze documents for health indicators
            doc_count = len(documents)
            
            # Count issues/findings
            finding_count = 0
            painpoint_count = 0
            
            for doc in documents:
                if not doc:
                    continue
                content_lower = doc.lower()
                
                # Count negative indicators
                if any(word in content_lower for word in ['issue', 'problem', 'error', 'bug', 'defect']):
                    finding_count += 1
                
                if any(word in content_lower for word in ['pain point', 'bottleneck', 'challenge', 'risk']):
                    painpoint_count += 1
            
            # Calculate scores (higher doc count and lower issues = better health)
            base_score = min(100, (doc_count / 10) * 100)  # More docs = more info = better
            issue_penalty = min(30, (finding_count + painpoint_count) * 2)
            
            process_health = max(50, base_score - issue_penalty)
            system_health = max(45, base_score - issue_penalty * 1.2)
            readiness_score = (process_health + system_health) / 2
            
            # Determine RAG status
            if readiness_score >= 80:
                rag_status = "Green"
            elif readiness_score >= 65:
                rag_status = "Yellow"
            elif readiness_score >= 50:
                rag_status = "Amber"
            else:
                rag_status = "Red"
            
            # Estimate value at stake (simplified)
            value_at_stake = int(base_score * 50000)  # Higher health = higher value
            
            return {
                "vs_code": vs_code,
                "process_health": round(process_health, 1),
                "system_health": round(system_health, 1),
                "readiness_score": round(readiness_score, 1),
                "value_at_stake_usd": value_at_stake,
                "rag_status": rag_status,
                "kpi_count": max(3, doc_count // 5),  # Estimate KPI count
                "finding_count": finding_count,
                "painpoint_count": painpoint_count
            }
            
        except Exception as e:
            logger.error(f"Error calculating health score for {vs_code}: {e}")
            return self._default_health_score(vs_code)
    
    def _default_health_score(self, vs_code: str) -> Dict:
        """Return default health score when calculation fails."""
        return {
            "vs_code": vs_code,
            "process_health": 75.0,
            "system_health": 70.0,
            "readiness_score": 72.5,
            "value_at_stake_usd": 1000000,
            "rag_status": "Yellow",
            "kpi_count": 5,
            "finding_count": 10,
            "painpoint_count": 5
        }
    
    def _extract_kpis_from_content(self, content: str, vs_code: str) -> List[Dict]:
        """
        Extract KPIs from document content using pattern matching.
        
        Args:
            content: Document content
            vs_code: Value stream code
            
        Returns:
            List of KPI dictionaries
        """
        kpis = []
        
        # KPI patterns to search for
        kpi_patterns = [
            r'([\w\s]+?(?:rate|time|score|percentage|ratio|count|cost|value))\s*[:\-]\s*(\d+(?:\.\d+)?)\s*(%|days|hours|USD|\$)?',
            r'KPI[:\s]+([\w\s]+?)[:\-]\s*(\d+(?:\.\d+)?)\s*(%|days|hours|USD|\$)?',
            r'Target[:\s]+([\w\s]+?)[:\-]\s*(\d+(?:\.\d+)?)\s*(%|days|hours|USD|\$)?',
        ]
        
        for pattern in kpi_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                kpi_name = match.group(1).strip()
                current_value = match.group(2)
                unit = match.group(3) if len(match.groups()) > 2 else ''
                
                # Skip if too short or too generic
                if len(kpi_name) < 5 or kpi_name.lower() in ['the', 'and', 'or', 'for']:
                    continue
                
                # Create KPI entry
                kpis.append({
                    "vs_code": vs_code,
                    "kpi_name": kpi_name.title(),
                    "current_value": f"{current_value}{unit or ''}",
                    "target_value": f"{float(current_value) * 1.2}{unit or ''}",  # 20% improvement target
                    "definition": f"Measures {kpi_name.lower()} for {vs_code} process",
                    "target_direction": "higher" if any(word in kpi_name.lower() for word in ['rate', 'score', 'success']) else "lower",
                    "current_numeric": float(current_value),
                    "target_numeric": float(current_value) * 1.2
                })
        
        return kpis[:5]  # Limit to 5 KPIs per document
