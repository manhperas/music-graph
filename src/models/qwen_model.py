"""
Qwen3 Model Integration for Music Knowledge Graph Chatbot.

This module provides:
- Qwen3-0.6B model loading with optional quantization
- LoRA adapter loading for fine-tuned models
- Inference pipeline for multi-hop reasoning
- Integration with GraphRAG context
"""

import os
import logging
from typing import Optional, Dict, Any, List, Union

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    GenerationConfig,
    BitsAndBytesConfig
)

logger = logging.getLogger(__name__)

# Default model configuration
DEFAULT_MODEL_NAME = "Qwen/Qwen3-0.6B"
INSTRUCT_MODEL_NAME = "Qwen/Qwen3-0.6B"


class Qwen3ModelLoader:
    """
    Utility class for loading Qwen3 models with various configurations.
    
    Supports:
    - Base model loading
    - Quantized model loading (4-bit, 8-bit)
    - LoRA adapter loading
    """
    
    @staticmethod
    def load_base_model(
        model_name: str = INSTRUCT_MODEL_NAME,
        device_map: str = "auto",
        torch_dtype: torch.dtype = torch.float16,
        quantization: Optional[str] = None,
        trust_remote_code: bool = True
    ) -> tuple:
        """
        Load base Qwen3 model and tokenizer.
        
        Args:
            model_name: HuggingFace model name or local path
            device_map: Device mapping strategy
            torch_dtype: Model precision
            quantization: Quantization mode ('4bit', '8bit', or None)
            trust_remote_code: Trust remote code flag
            
        Returns:
            Tuple of (model, tokenizer)
        """
        logger.info(f"Loading model: {model_name}")
        
        # Configure quantization if requested
        quantization_config = None
        if quantization == "4bit":
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            logger.info("Using 4-bit quantization")
        elif quantization == "8bit":
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True
            )
            logger.info("Using 8-bit quantization")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=trust_remote_code
        )
        
        # Ensure pad token is set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        
        # Load model
        model_kwargs = {
            "trust_remote_code": trust_remote_code,
            "device_map": device_map,
        }
        
        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
        else:
            model_kwargs["torch_dtype"] = torch_dtype
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            **model_kwargs
        )
        
        logger.info(f"Model loaded successfully on device: {model.device}")
        
        return model, tokenizer
    
    @staticmethod
    def load_with_lora(
        base_model_name: str = INSTRUCT_MODEL_NAME,
        lora_path: str = None,
        device_map: str = "auto",
        torch_dtype: torch.dtype = torch.float16,
        quantization: Optional[str] = None
    ) -> tuple:
        """
        Load model with LoRA adapter.
        
        Args:
            base_model_name: Base model name
            lora_path: Path to LoRA adapter
            device_map: Device mapping
            torch_dtype: Model precision
            quantization: Quantization mode
            
        Returns:
            Tuple of (model, tokenizer)
        """
        from peft import PeftModel
        
        # Load base model
        model, tokenizer = Qwen3ModelLoader.load_base_model(
            model_name=base_model_name,
            device_map=device_map,
            torch_dtype=torch_dtype,
            quantization=quantization
        )
        
        if lora_path and os.path.exists(lora_path):
            logger.info(f"Loading LoRA adapter from: {lora_path}")
            model = PeftModel.from_pretrained(model, lora_path)
            model = model.merge_and_unload()  # Merge for faster inference
            logger.info("LoRA adapter loaded and merged")
        else:
            logger.warning(f"LoRA path not found: {lora_path}, using base model")
        
        return model, tokenizer


class Qwen3MusicChatbot:
    """
    Music Knowledge Graph Chatbot powered by Qwen3.
    
    Features:
    - Multi-hop reasoning with GraphRAG context
    - Streaming generation support
    - Configurable generation parameters
    """
    
    # System prompt for music domain
    SYSTEM_PROMPT = """You are a music knowledge assistant. You answer questions about musicians, bands, albums, songs, genres, awards, and collaborations.

When given context from a music knowledge graph, use it to answer questions accurately. If the context doesn't contain enough information, say so clearly.

For yes/no questions, start your answer with "Yes" or "No" followed by a brief explanation.
For factual questions, provide concise and accurate answers based on the context."""

    def __init__(
        self,
        model_name: str = INSTRUCT_MODEL_NAME,
        lora_path: Optional[str] = None,
        device_map: str = "auto",
        torch_dtype: torch.dtype = torch.float16,
        quantization: Optional[str] = None,
        max_new_tokens: int = 256,
        temperature: float = 0.1,
        top_p: float = 0.9,
        do_sample: bool = True
    ):
        """
        Initialize the chatbot.
        
        Args:
            model_name: HuggingFace model name
            lora_path: Optional path to LoRA adapter
            device_map: Device mapping strategy
            torch_dtype: Model precision
            quantization: Quantization mode
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            do_sample: Whether to use sampling
        """
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.do_sample = do_sample
        
        # Load model
        if lora_path:
            self.model, self.tokenizer = Qwen3ModelLoader.load_with_lora(
                base_model_name=model_name,
                lora_path=lora_path,
                device_map=device_map,
                torch_dtype=torch_dtype,
                quantization=quantization
            )
        else:
            self.model, self.tokenizer = Qwen3ModelLoader.load_base_model(
                model_name=model_name,
                device_map=device_map,
                torch_dtype=torch_dtype,
                quantization=quantization
            )
        
        # Set model to eval mode
        self.model.eval()
        
        # Configure generation
        self.generation_config = GenerationConfig(
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id
        )
        
        logger.info("Qwen3MusicChatbot initialized successfully")
    
    def _build_prompt(
        self,
        question: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Build chat prompt with context.
        
        Args:
            question: User question
            context: GraphRAG context
            system_prompt: Optional custom system prompt
            
        Returns:
            Formatted prompt string
        """
        system = system_prompt or self.SYSTEM_PROMPT
        
        if context:
            user_content = f"""Context from music knowledge graph:
{context}

Question: {question}

Please answer based on the context provided."""
        else:
            user_content = question
        
        # Build messages for chat template
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content}
        ]
        
        # Apply chat template
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        return prompt
    
    def generate(
        self,
        question: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate answer for a question.
        
        Args:
            question: User question
            context: GraphRAG context
            system_prompt: Optional custom system prompt
            max_new_tokens: Override max tokens
            temperature: Override temperature
            **kwargs: Additional generation parameters
            
        Returns:
            Generated answer string
        """
        # Build prompt
        prompt = self._build_prompt(question, context, system_prompt)
        
        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(self.model.device)
        
        # Update generation config if needed
        gen_config = GenerationConfig(
            max_new_tokens=max_new_tokens or self.max_new_tokens,
            temperature=temperature or self.temperature,
            top_p=self.top_p,
            do_sample=self.do_sample,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            **kwargs
        )
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                generation_config=gen_config
            )
        
        # Decode only new tokens
        input_length = inputs['input_ids'].shape[1]
        generated_tokens = outputs[0][input_length:]
        answer = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        
        return answer.strip()
    
    def answer_with_graph_context(
        self,
        question: str,
        graph_retriever,
        max_hops: int = 3
    ) -> Dict[str, Any]:
        """
        Answer question using GraphRAG retrieval.
        
        Args:
            question: User question
            graph_retriever: GraphRAGRetriever instance
            max_hops: Maximum hops for path finding
            
        Returns:
            Dictionary with answer and metadata
        """
        # Retrieve context from graph
        retrieval_result = graph_retriever.retrieve_context(question, max_hops=max_hops)
        
        context = retrieval_result.get('context_text', '')
        
        # Generate answer
        answer = self.generate(question, context=context)
        
        return {
            'question': question,
            'answer': answer,
            'context': context,
            'entities': retrieval_result.get('entities', []),
            'paths': retrieval_result.get('paths', []),
            'paths_count': retrieval_result.get('all_paths_count', 0)
        }
    
    def batch_generate(
        self,
        questions: List[str],
        contexts: Optional[List[str]] = None,
        batch_size: int = 4
    ) -> List[str]:
        """
        Generate answers for multiple questions.
        
        Args:
            questions: List of questions
            contexts: Optional list of contexts
            batch_size: Batch size for generation
            
        Returns:
            List of generated answers
        """
        answers = []
        contexts = contexts or [None] * len(questions)
        
        for i in range(0, len(questions), batch_size):
            batch_questions = questions[i:i+batch_size]
            batch_contexts = contexts[i:i+batch_size]
            
            for q, c in zip(batch_questions, batch_contexts):
                answer = self.generate(q, context=c)
                answers.append(answer)
        
        return answers


def create_chatbot(
    model_name: str = INSTRUCT_MODEL_NAME,
    lora_path: Optional[str] = None,
    quantization: Optional[str] = None,
    **kwargs
) -> Qwen3MusicChatbot:
    """
    Factory function to create a chatbot instance.
    
    Args:
        model_name: Model name or path
        lora_path: Optional LoRA adapter path
        quantization: Quantization mode ('4bit', '8bit', or None)
        **kwargs: Additional chatbot parameters
        
    Returns:
        Configured Qwen3MusicChatbot instance
    """
    return Qwen3MusicChatbot(
        model_name=model_name,
        lora_path=lora_path,
        quantization=quantization,
        **kwargs
    )


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Qwen3 Model Loader...")
    print(f"Default model: {INSTRUCT_MODEL_NAME}")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")


