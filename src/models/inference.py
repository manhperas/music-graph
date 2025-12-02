"""
Inference utilities for Music Knowledge Graph Chatbot.

This module provides:
- Batched inference for efficient processing
- Streaming generation support
- Integration with GraphRAG retriever
"""

import os
import logging
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass

import torch
from transformers import TextIteratorStreamer
from threading import Thread

logger = logging.getLogger(__name__)


@dataclass
class InferenceConfig:
    """Configuration for inference."""
    max_new_tokens: int = 256
    temperature: float = 0.1
    top_p: float = 0.9
    top_k: int = 50
    do_sample: bool = True
    repetition_penalty: float = 1.1


class BatchedInference:
    """
    Batched inference for efficient processing of multiple queries.
    """
    
    def __init__(self, chatbot, batch_size: int = 4):
        """
        Initialize batched inference.
        
        Args:
            chatbot: Qwen3MusicChatbot instance
            batch_size: Maximum batch size
        """
        self.chatbot = chatbot
        self.batch_size = batch_size
        self.model = chatbot.model
        self.tokenizer = chatbot.tokenizer
    
    def process_batch(
        self,
        questions: List[str],
        contexts: Optional[List[str]] = None,
        config: Optional[InferenceConfig] = None
    ) -> List[str]:
        """
        Process a batch of questions.
        
        Args:
            questions: List of questions
            contexts: Optional list of contexts
            config: Inference configuration
            
        Returns:
            List of generated answers
        """
        config = config or InferenceConfig()
        contexts = contexts or [None] * len(questions)
        
        answers = []
        
        # Process in batches
        for i in range(0, len(questions), self.batch_size):
            batch_questions = questions[i:i + self.batch_size]
            batch_contexts = contexts[i:i + self.batch_size]
            
            batch_answers = self._process_single_batch(
                batch_questions, batch_contexts, config
            )
            answers.extend(batch_answers)
        
        return answers
    
    def _process_single_batch(
        self,
        questions: List[str],
        contexts: List[Optional[str]],
        config: InferenceConfig
    ) -> List[str]:
        """Process a single batch."""
        # Build prompts
        prompts = []
        for q, c in zip(questions, contexts):
            prompt = self.chatbot._build_prompt(q, c)
            prompts.append(prompt)
        
        # Tokenize with padding
        inputs = self.tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=2048
        ).to(self.model.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=config.max_new_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                do_sample=config.do_sample,
                repetition_penalty=config.repetition_penalty,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode answers
        answers = []
        for i, output in enumerate(outputs):
            input_length = inputs['input_ids'][i].ne(self.tokenizer.pad_token_id).sum()
            generated_tokens = output[input_length:]
            answer = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
            answers.append(answer.strip())
        
        return answers


class StreamingInference:
    """
    Streaming inference for real-time response generation.
    """
    
    def __init__(self, chatbot):
        """
        Initialize streaming inference.
        
        Args:
            chatbot: Qwen3MusicChatbot instance
        """
        self.chatbot = chatbot
        self.model = chatbot.model
        self.tokenizer = chatbot.tokenizer
    
    def generate_stream(
        self,
        question: str,
        context: Optional[str] = None,
        config: Optional[InferenceConfig] = None
    ) -> Generator[str, None, None]:
        """
        Generate answer with streaming output.
        
        Args:
            question: User question
            context: Optional context
            config: Inference configuration
            
        Yields:
            Generated tokens as they are produced
        """
        config = config or InferenceConfig()
        
        # Build prompt
        prompt = self.chatbot._build_prompt(question, context)
        
        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(self.model.device)
        
        # Create streamer
        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )
        
        # Generation kwargs
        generation_kwargs = {
            **inputs,
            "streamer": streamer,
            "max_new_tokens": config.max_new_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "do_sample": config.do_sample,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id
        }
        
        # Start generation in separate thread
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()
        
        # Yield tokens as they are generated
        for text in streamer:
            yield text
        
        thread.join()


class GraphRAGInference:
    """
    Inference with automatic GraphRAG context retrieval.
    """
    
    def __init__(self, chatbot, graph_retriever):
        """
        Initialize GraphRAG inference.
        
        Args:
            chatbot: Qwen3MusicChatbot instance
            graph_retriever: GraphRAGRetriever instance
        """
        self.chatbot = chatbot
        self.retriever = graph_retriever
    
    def answer(
        self,
        question: str,
        max_hops: int = 3,
        config: Optional[InferenceConfig] = None
    ) -> Dict[str, Any]:
        """
        Answer question with automatic context retrieval.
        
        Args:
            question: User question
            max_hops: Maximum hops for path finding
            config: Inference configuration
            
        Returns:
            Dictionary with answer and metadata
        """
        # Retrieve context
        retrieval_result = self.retriever.retrieve_context(question, max_hops=max_hops)
        context = retrieval_result.get('context_text', '')
        
        # Generate answer
        if config:
            answer = self.chatbot.generate(
                question,
                context=context,
                max_new_tokens=config.max_new_tokens,
                temperature=config.temperature
            )
        else:
            answer = self.chatbot.generate(question, context=context)
        
        return {
            'question': question,
            'answer': answer,
            'context': context,
            'entities': retrieval_result.get('entities', []),
            'paths': retrieval_result.get('paths', []),
            'paths_count': retrieval_result.get('all_paths_count', 0)
        }
    
    def batch_answer(
        self,
        questions: List[str],
        max_hops: int = 3,
        config: Optional[InferenceConfig] = None
    ) -> List[Dict[str, Any]]:
        """
        Answer multiple questions with context retrieval.
        
        Args:
            questions: List of questions
            max_hops: Maximum hops for path finding
            config: Inference configuration
            
        Returns:
            List of answer dictionaries
        """
        results = []
        
        for question in questions:
            result = self.answer(question, max_hops=max_hops, config=config)
            results.append(result)
        
        return results


# Convenience functions

def create_inference_pipeline(
    model_name: str = "Qwen/Qwen3-0.6B",
    lora_path: Optional[str] = None,
    quantization: Optional[str] = "4bit",
    neo4j_driver = None
) -> Dict[str, Any]:
    """
    Create a complete inference pipeline.
    
    Args:
        model_name: Base model name
        lora_path: Path to LoRA adapter
        quantization: Quantization mode
        neo4j_driver: Optional Neo4j driver for GraphRAG
        
    Returns:
        Dictionary with chatbot and inference utilities
    """
    from .qwen_model import Qwen3MusicChatbot
    
    # Create chatbot
    chatbot = Qwen3MusicChatbot(
        model_name=model_name,
        lora_path=lora_path,
        quantization=quantization
    )
    
    # Create inference utilities
    pipeline = {
        'chatbot': chatbot,
        'batched': BatchedInference(chatbot),
        'streaming': StreamingInference(chatbot)
    }
    
    # Add GraphRAG if driver provided
    if neo4j_driver:
        from src.graph_rag import GraphRAGRetriever
        retriever = GraphRAGRetriever(neo4j_driver)
        pipeline['graphrag'] = GraphRAGInference(chatbot, retriever)
    
    return pipeline


