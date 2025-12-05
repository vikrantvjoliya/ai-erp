"""
Main Orchestration Pipeline for ERP Modernization Health Check.
Coordinates all analysis modules and generates comprehensive reports.
"""
from typing import List, Dict, Optional
from pathlib import Path
from loguru import logger

from langchain.schema import Document

from config import Config, get_config
from data_ingestion import DataIngestionPipeline
from process_mining import ProcessMiningEngine
from sentiment_analysis import SentimentAnalyzer
from benchmarking import BenchmarkingEngine
from risk_assessment import RiskAssessmentEngine
from visualization import VisualizationEngine
from vector_store import VectorStore
from text_processor import TextProcessor


class ERPHealthCheckPipeline:
    """Main orchestration pipeline for ERP modernization health check."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the health check pipeline.
        
        Args:
            config: Configuration object
        """
        self.config = config or get_config()
        
        # Initialize components
        logger.info("Initializing ERP Health Check Pipeline...")
        
        self.data_ingestion = DataIngestionPipeline(self.config)
        # Pass numeric chunking settings from config into TextProcessor
        self.text_processor = TextProcessor(
            chunk_size=self.config.chunking.chunk_size,
            chunk_overlap=self.config.chunking.chunk_overlap
        )
        self.vector_store = VectorStore(self.config)
        self.process_mining = ProcessMiningEngine(
            min_variant_frequency=self.config.analysis.min_variant_frequency
        )
        self.sentiment_analyzer = SentimentAnalyzer(
            model_name=self.config.analysis.sentiment_model,
            # Disable transformers use by default to avoid native crashes on some setups.
            # Falls back to TextBlob which is pure-Python and stable.
            use_transformers=False
        )
        self.benchmarking = BenchmarkingEngine(
            benchmark_threshold=self.config.analysis.benchmark_threshold
        )
        self.risk_assessment = RiskAssessmentEngine(
            risk_weights=self.config.analysis.risk_weights
        )
        self.visualization = VisualizationEngine(self.config)
        
        # Initialize RAG system (lazy loading)
        self.rag_system: Optional['RAGSystem'] = None
        
        logger.info("Pipeline initialized successfully")
    
    def _init_rag_system(self) -> None:
        """Initialize RAG system if not already initialized."""
        if self.rag_system is None:
            logger.info("Initializing RAG system...")
            try:
                from rag_system_updated import RAGSystem
                
                # Load vector store if not loaded
                if self.vector_store.vectorstore is None:
                    self.vector_store.load_vectorstore()
                
                self.rag_system = RAGSystem(
                    vector_store=self.vector_store,
                    config=self.config
                )
                logger.info("RAG system initialized")
            except Exception as e:
                logger.error(f"Failed to initialize RAG system: {e}")
                raise
    
    def run_full_analysis(
        self,
        input_directory: Optional[str] = None,
        create_vector_store: bool = True
    ) -> Dict:
        """
        Run complete health check analysis pipeline.
        
        Args:
            input_directory: Directory containing input files
            create_vector_store: Whether to create/update vector store
            
        Returns:
            Complete analysis results
        """
        logger.info("=" * 60)
        logger.info("Starting ERP Modernization Health Check Analysis")
        logger.info("=" * 60)
        
        results = {}
        
        # Step 1: Data Ingestion & Harmonization
        logger.info("\n[1/7] Data Ingestion & Harmonization")
        documents = self.data_ingestion.ingest_directory(input_directory)
        
        if not documents:
            logger.error("No documents ingested. Cannot proceed with analysis.")
            return {"error": "No documents found for analysis"}
        
        harmonized_docs = self.data_ingestion.harmonize_data(documents)
        results["ingestion_stats"] = self.data_ingestion.get_statistics()
        
        logger.info(f"Ingested and harmonized {len(harmonized_docs)} documents")
        
        # Step 2: Text Processing & Chunking
        logger.info("\n[2/7] Text Processing & Chunking")
        chunked_docs = self.text_processor.process_documents(harmonized_docs)
        
        logger.info(f"Processed into {len(chunked_docs)} chunks")
        
        # Step 3: Vector Store Creation (if enabled)
        if create_vector_store:
            logger.info("\n[3/7] Creating Vector Store")
            try:
                self.vector_store.create_vectorstore(chunked_docs)
                results["vector_store_stats"] = self.vector_store.get_collection_stats()
            except Exception as e:
                logger.error(f"Vector store creation failed: {e}")
                results["vector_store_error"] = str(e)
        else:
            logger.info("\n[3/7] Skipping Vector Store Creation")
        
        # Step 4: Process Mining & Discovery
        logger.info("\n[4/7] Process Mining & Discovery")
        process_results = self.process_mining.analyze_process_maps(harmonized_docs)
        results["process_mining"] = process_results
        
        # Step 5: Pain Point & Sentiment Analysis
        logger.info("\n[5/7] Pain Point & Sentiment Analysis")
        sentiment_results = self.sentiment_analyzer.analyze_documents(harmonized_docs)
        results["sentiment"] = sentiment_results
        
        # Step 6: Benchmarking & Value Driver Analysis
        logger.info("\n[6/7] Benchmarking & Value Driver Analysis")
        benchmark_results = self.benchmarking.analyze_benchmarks(harmonized_docs)
        results["benchmarking"] = benchmark_results
        
        # Step 7: Risk & Readiness Assessment
        logger.info("\n[7/7] Risk & Readiness Assessment")
        risk_results = self.risk_assessment.assess_risks(harmonized_docs)
        results["risk"] = risk_results
        
        logger.info("\n" + "=" * 60)
        logger.info("Analysis Complete!")
        logger.info("=" * 60)
        
        return results
    
    def generate_visualizations(self, results: Dict) -> Dict:
        """
        Generate all visualizations and reports.
        
        Args:
            results: Analysis results from run_full_analysis
            
        Returns:
            Dictionary of generated file paths
        """
        logger.info("\nGenerating Visualizations and Reports...")
        
        generated_files = {}
        
        try:
            # Pain point heatmap
            if results.get("sentiment", {}).get("heatmap_data"):
                path = self.visualization.generate_pain_point_heatmap(
                    results["sentiment"]["heatmap_data"]
                )
                generated_files["pain_point_heatmap"] = path
            
            # Risk heatmap
            if results.get("risk", {}).get("risk_heatmap"):
                path = self.visualization.generate_risk_heatmap(
                    results["risk"]["risk_heatmap"]
                )
                generated_files["risk_heatmap"] = path
            
            # Sentiment dashboard
            if results.get("sentiment"):
                path = self.visualization.generate_sentiment_dashboard(
                    results["sentiment"]
                )
                generated_files["sentiment_dashboard"] = path
            
            # Benchmark dashboard
            if results.get("benchmarking"):
                path = self.visualization.generate_benchmark_dashboard(
                    results["benchmarking"]
                )
                generated_files["benchmark_dashboard"] = path
            
            # Readiness gauge
            if results.get("risk", {}).get("readiness_score"):
                path = self.visualization.generate_readiness_gauge(
                    results["risk"]["readiness_score"]
                )
                generated_files["readiness_gauge"] = path
            
            # Executive report
            path = self.visualization.generate_executive_report(results)
            generated_files["executive_report"] = path
            
            # JSON export
            path = self.visualization.export_json_report(results)
            generated_files["json_report"] = path
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {e}")
            generated_files["error"] = str(e)
        
        logger.info(f"Generated {len(generated_files)} visualization files")
        
        return generated_files
    
    def generate_summary_report(self, results: Dict) -> str:
        """
        Generate a text summary report.
        
        Args:
            results: Analysis results
            
        Returns:
            Summary report string
        """
        report_lines = [
            "=" * 80,
            "ERP MODERNIZATION HEALTH CHECK - SUMMARY REPORT",
            "=" * 80,
            ""
        ]
        
        # Ingestion Stats
        if "ingestion_stats" in results:
            stats = results["ingestion_stats"]
            report_lines.extend([
                "DATA INGESTION:",
                f"  Total Files Processed: {stats.get('total_files', 0)}",
                f"  Successful: {stats.get('successful', 0)}",
                f"  Failed: {stats.get('failed', 0)}",
                ""
            ])
        
        # Sentiment Analysis
        if "sentiment" in results:
            sentiment = results["sentiment"]
            overall = sentiment.get("overall_sentiment", {})
            report_lines.extend([
                "SENTIMENT ANALYSIS:",
                f"  Average Sentiment: {overall.get('average_score', 0):.3f}",
                f"  Negative Ratio: {overall.get('negative_ratio', 0):.1%}",
                f"  Pain Points Identified: {len(sentiment.get('pain_points', []))}",
                ""
            ])
        
        # Process Mining
        if "process_mining" in results:
            process = results["process_mining"]
            report_lines.extend([
                "PROCESS MINING:",
                f"  Total Processes Analyzed: {process.get('total_processes', 0)}",
                f"  Process Variants Found: {len(process.get('variants', []))}",
                f"  Bottlenecks Identified: {len(process.get('bottlenecks', []))}",
                ""
            ])
        
        # Benchmarking
        if "benchmarking" in results:
            benchmark = results["benchmarking"]
            gaps = benchmark.get('gaps', [])
            report_lines.extend([
                "BENCHMARKING:",
                f"  Gaps Identified: {len(gaps)}",
                f"  High Priority Gaps: {sum(1 for g in gaps if g.get('priority', 0) > 70)}",
                ""
            ])
        
        # Risk Assessment
        if "risk" in results:
            risk = results["risk"]
            summary = risk.get("risk_summary", {})
            readiness = risk.get("readiness_score", {})
            report_lines.extend([
                "RISK ASSESSMENT:",
                f"  Total Risks Found: {summary.get('total_findings', 0)}",
                f"  Critical Findings: {summary.get('critical_findings', 0)}",
                f"  Overall Risk Score: {summary.get('overall_risk_score', 0):.1f}",
                f"  Readiness Score: {readiness.get('overall_score', 0):.1f}%",
                f"  Readiness Status: {readiness.get('status', 'unknown').upper()}",
                ""
            ])
        
        report_lines.extend([
            "=" * 80,
            "For detailed analysis, see the generated visualizations and reports.",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def query_knowledge_base(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: Optional[int] = None,
        use_rag: bool = True
    ) -> Dict:
        """
        Query the knowledge base using RAG or simple vector search.
        
        Args:
            query: Query string
            category: Optional category filter
            top_k: Number of results to return
            use_rag: Whether to use RAG (True) or simple search (False)
            
        Returns:
            Query results with answer and sources
        """
        if self.vector_store.vectorstore is None:
            logger.warning("Vector store not initialized. Loading...")
            try:
                self.vector_store.load_vectorstore()
            except FileNotFoundError:
                logger.error("No vector store found. Please run full analysis first.")
                return {
                    "error": "No vector store found",
                    "message": "Please run full analysis first to create the knowledge base"
                }
        
        if use_rag:
            # Use RAG for intelligent question answering
            try:
                self._init_rag_system()
                result = self.rag_system.query(query, return_source=True)
                return result
            except Exception as e:
                logger.error(f"RAG query failed: {e}. Falling back to vector search.")
                use_rag = False
        
        # Fallback to simple vector search
        if category:
            docs = self.vector_store.search_by_category(query, category, k=top_k)
        else:
            docs = self.vector_store.similarity_search(query, k=top_k)
        
        return {
            "query": query,
            "answer": "Vector search results (RAG not available)",
            "source_documents": docs,
            "sources": [
                {
                    "index": idx + 1,
                    "source": doc.metadata.get("source", "Unknown"),
                    "category": doc.metadata.get("category", "N/A"),
                    "content_preview": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                    "metadata": doc.metadata
                }
                for idx, doc in enumerate(docs)
            ]
        }
    
    def ask_question(self, question: str) -> str:
        """
        Simple Q&A interface using RAG.
        
        Args:
            question: Question to ask
            
        Returns:
            Answer string
        """
        self._init_rag_system()
        return self.rag_system.chat(question)


# Convenience function for quick execution
def run_health_check(
    input_directory: str = "./data/input",
    output_directory: str = "./data/output",
    config_file: Optional[str] = None
) -> Dict:
    """
    Convenience function to run complete health check.
    
    Args:
        input_directory: Input data directory
        output_directory: Output directory for results
        config_file: Optional configuration file
        
    Returns:
        Analysis results and generated files
    """
    # Initialize configuration
    if config_file:
        config = Config.from_yaml(config_file)
    else:
        config = get_config()
    
    # Create pipeline
    pipeline = ERPHealthCheckPipeline(config)
    
    # Run analysis
    results = pipeline.run_full_analysis(input_directory, create_vector_store=True)
    
    # Generate visualizations
    generated_files = pipeline.generate_visualizations(results)
    
    # Generate summary
    summary = pipeline.generate_summary_report(results)
    print("\n" + summary)
    
    return {
        "results": results,
        "generated_files": generated_files,
        "summary": summary
    }
