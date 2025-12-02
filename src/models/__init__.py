"""
Models module for Music Knowledge Graph Chatbot.

This module provides LLM integration with Qwen3 for:
- Text generation
- Multi-hop reasoning
- Question answering with GraphRAG context
"""

from .qwen_model import Qwen3MusicChatbot, Qwen3ModelLoader, create_chatbot
from .inference import (
    BatchedInference,
    StreamingInference,
    GraphRAGInference,
    InferenceConfig,
    create_inference_pipeline
)

__all__ = [
    'Qwen3MusicChatbot',
    'Qwen3ModelLoader',
    'create_chatbot',
    'BatchedInference',
    'StreamingInference',
    'GraphRAGInference',
    'InferenceConfig',
    'create_inference_pipeline'
]

