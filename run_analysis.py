"""
Simple CLI script to run the ERP Health Check analysis.
"""
import argparse
from pathlib import Path
from loguru import logger
import sys

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

from pipeline import run_health_check
from config import Config


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ERP Modernization Health Check - CLI Tool"
    )
    
    parser.add_argument(
        "-i", "--input",
        default="./data/input",
        help="Input directory containing documents (default: ./data/input)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="./data/output",
        help="Output directory for reports (default: ./data/output)"
    )
    
    parser.add_argument(
        "-c", "--config",
        default=None,
        help="Path to configuration file (optional)"
    )
    
    parser.add_argument(
        "--no-vector-store",
        action="store_true",
        help="Skip vector store creation"
    )
    
    parser.add_argument(
        "--query",
        help="Query the knowledge base (requires existing vector store)"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        config = Config.from_yaml(args.config)
        logger.info(f"Loaded configuration from {args.config}")
    else:
        config = Config()
        logger.info("Using default configuration")
    
    # Handle query mode
    if args.query:
        from pipeline import ERPHealthCheckPipeline
        
        logger.info(f"Querying knowledge base: {args.query}")
        pipeline = ERPHealthCheckPipeline(config)
        
        try:
            results = pipeline.query_knowledge_base(args.query)
            
            print("\n" + "=" * 80)
            print(f"QUERY: {args.query}")
            print("=" * 80)
            
            for idx, doc in enumerate(results, 1):
                print(f"\n[{idx}] Source: {doc.metadata.get('source', 'Unknown')}")
                print(f"Category: {doc.metadata.get('category', 'N/A')}")
                print(f"Content: {doc.page_content[:500]}...")
                print("-" * 80)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            sys.exit(1)
        
        return
    
    # Run full analysis
    logger.info("Starting ERP Modernization Health Check Analysis...")
    logger.info(f"Input directory: {args.input}")
    logger.info(f"Output directory: {args.output}")
    
    try:
        result = run_health_check(
            input_directory=args.input,
            output_directory=args.output,
            config_file=args.config
        )
        
        logger.success("Analysis completed successfully!")
        logger.info(f"Reports generated in: {args.output}")
        
        # Print summary
        print("\n" + result["summary"])
        
        # Print generated files
        print("\nGenerated Files:")
        for name, path in result["generated_files"].items():
            if path:
                print(f"  - {name}: {path}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
