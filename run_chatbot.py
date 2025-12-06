#!/usr/bin/env python3
"""
Run the Music Knowledge Graph Chatbot.

Usage:
    # Run Gradio UI (demo mode, no model)
    python run_chatbot.py --ui gradio
    
    # Run Gradio UI (with model)
    python run_chatbot.py --ui gradio --load-model
    
    # Run FastAPI server
    python run_chatbot.py --ui api
    
    # Run both
    python run_chatbot.py --ui both
"""

import os
import sys
import argparse
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_gradio(args):
    """Run Gradio UI."""
    from src.api.gradio_app import launch_gradio
    
    chatbot = None
    retriever = None
    
    if args.load_model:
        try:
            from src.models.qwen_model import Qwen3MusicChatbot
            
            logger.info("Loading chatbot model...")
            chatbot = Qwen3MusicChatbot(
                model_name="Qwen/Qwen3-0.6B",
                lora_path=args.lora_path,
                quantization="4bit" if not args.no_quantize else None
            )
            logger.info("✅ Model loaded!")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load model: {e}")
            logger.info("Running in demo mode...")
    
    # Connect to Neo4j if requested
    if args.use_neo4j:
        try:
            from neo4j import GraphDatabase
            from src.graph_rag import GraphRAGRetriever
            
            neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
            neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
            neo4j_pass = os.getenv('NEO4J_PASS', 'password')
            
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
            retriever = GraphRAGRetriever(driver)
            logger.info("✅ Neo4j connected!")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to Neo4j: {e}")
    
    launch_gradio(
        chatbot=chatbot,
        graph_retriever=retriever,
        port=args.port,
        share=args.share
    )


def run_api(args):
    """Run FastAPI server."""
    import uvicorn
    
    # Set environment variables
    if args.lora_path:
        os.environ['LORA_PATH'] = args.lora_path
    if args.use_neo4j:
        os.environ['USE_NEO4J'] = 'true'
    
    logger.info(f"Starting FastAPI server on port {args.api_port}...")
    
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=args.api_port,
        reload=args.reload,
        log_level="info"
    )


def run_both(args):
    """Run both Gradio and API."""
    import threading
    import time
    
    # Start API in background thread
    api_thread = threading.Thread(
        target=run_api,
        args=(args,),
        daemon=True
    )
    api_thread.start()
    
    time.sleep(2)  # Wait for API to start
    
    # Run Gradio in main thread
    run_gradio(args)


def main():
    parser = argparse.ArgumentParser(
        description="Run Music Knowledge Graph Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Demo mode (no model required)
    python run_chatbot.py --ui gradio
    
    # With model loaded
    python run_chatbot.py --ui gradio --load-model
    
    # With custom LoRA path
    python run_chatbot.py --ui gradio --load-model --lora-path /path/to/lora
    
    # FastAPI server
    python run_chatbot.py --ui api
    
    # With Neo4j graph
    python run_chatbot.py --ui gradio --load-model --use-neo4j
        """
    )
    
    # UI selection
    parser.add_argument(
        "--ui",
        choices=["gradio", "api", "both"],
        default="gradio",
        help="Which UI to run (default: gradio)"
    )
    
    # Model options
    parser.add_argument(
        "--load-model",
        action="store_true",
        help="Load the actual Qwen model (requires GPU)"
    )
    parser.add_argument(
        "--lora-path",
        type=str,
        default=None,
        help="Path to LoRA adapter (optional)"
    )
    parser.add_argument(
        "--no-quantize",
        action="store_true",
        help="Disable 4-bit quantization"
    )
    
    # Graph options
    parser.add_argument(
        "--use-neo4j",
        action="store_true",
        help="Connect to Neo4j for graph context"
    )
    
    # Server options
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Gradio port (default: 7860)"
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8000,
        help="API port (default: 8000)"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create public Gradio link"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for API"
    )
    
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║     🎵 Music Knowledge Graph Chatbot                         ║
║                                                              ║
║     Powered by Qwen3 + LoRA + GraphRAG                       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if args.ui == "gradio":
        run_gradio(args)
    elif args.ui == "api":
        run_api(args)
    elif args.ui == "both":
        run_both(args)


if __name__ == "__main__":
    main()





