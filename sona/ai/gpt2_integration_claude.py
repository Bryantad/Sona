"""
GPT-2 Integration Layer for Claude-like Chatbot
==============================================

Optimized GPT-2 integration that leverages Sona's existing CUDA infrastructure
to deliver high-performance conversational AI with Claude-like response patterns.
"""

import asyncio
import gc
import logging
import time
from typing import Dict, List, Tuple

import psutil
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer


logger = logging.getLogger(__name__)


class GPT2Integration:
    """
    High-performance GPT-2 integration optimized for conversational AI
    """
    
    def __init__(self, model_path: str = None, cuda_device: int = 0):
        self.model_path = model_path or "F:/Sona/models/gpt2"
        self.device = f"cuda:{cuda_device}" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        
        # Performance tracking
        self.performance_metrics = {
            'total_generations': 0,
            'total_time': 0.0,
            'average_response_time': 0.0,
            'memory_usage': 0,
            'cuda_utilization': 0.0
        }
        
        # Conversation optimization parameters
        self.conversation_config = {
            'max_length': 512,
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 50,
            'repetition_penalty': 1.1,
            'do_sample': True
        }
        
        logger.info(f"Initializing GPT-2 Integration with device: {self.device}")
        
    def initialize_model(self):
        """Initialize and load the GPT-2 model"""
        try:
            logger.info(f"Loading GPT-2 model from {self.model_path}")
            
            # Load tokenizer
            self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_path)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.model = GPT2LMHeadModel.from_pretrained(self.model_path)
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode for inference
            
            # Optimize for conversation
            self.optimize_for_conversation()
            
            logger.info(f"✅ GPT-2 model loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load GPT-2 model: {str(e)}")
            return False
    
    async def generate_text(self, 
                          prompt: str, 
                          max_tokens: int = 150,
                          temperature: float = 0.7,
                          top_p: float = 0.9) -> tuple[str, dict]:
        """
        Generate text using CUDA-optimized GPT-2
        Returns: (generated_text, metrics)
        """
        start_time = time.time()
        
        if self.model is None:
            if not self.initialize_model():
                raise RuntimeError("Failed to initialize GPT-2 model")
        
        try:
            # Tokenize input
            inputs = self.tokenizer.encode(prompt, return_tensors='pt', truncate=True, max_length=400)
            inputs = inputs.to(self.device)
            
            # Generate text
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=self.conversation_config['top_k'],
                    repetition_penalty=self.conversation_config['repetition_penalty'],
                    do_sample=self.conversation_config['do_sample'],
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new generated part
            generated_text = generated_text[len(prompt):].strip()
            
            # Calculate metrics
            generation_time = time.time() - start_time
            metrics = self._calculate_generation_metrics(generation_time, len(generated_text))
            
            # Update performance tracking
            self._update_performance_metrics(generation_time)
            
            logger.debug(f"Generated text in {generation_time:.3f}s: {len(generated_text)} characters")
            
            return generated_text, metrics
            
        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}")
            generation_time = time.time() - start_time
            return "I apologize, but I'm having trouble generating a response right now.", {
                'generation_time': generation_time,
                'error': str(e)
            }
    
    def optimize_for_conversation(self):
        """Optimize model parameters for conversational use"""
        if self.model is None:
            return
        
        try:
            # Enable optimizations for inference
            if hasattr(torch.nn.functional, 'scaled_dot_product_attention'):
                # Use Flash Attention if available
                self.model = torch.compile(self.model, mode="reduce-overhead")
            
            # Set optimal conversation parameters
            self.conversation_config.update({
                'temperature': 0.7,  # Balanced creativity and coherence
                'top_p': 0.9,       # Good diversity while staying on topic
                'repetition_penalty': 1.1  # Reduce repetition
            })
            
            logger.info("✅ Model optimized for conversational use")
            
        except Exception as e:
            logger.warning(f"Could not apply all optimizations: {str(e)}")
    
    def _calculate_generation_metrics(self, generation_time: float, text_length: int) -> dict:
        """Calculate detailed generation metrics"""
        tokens_per_second = (text_length / 4) / generation_time  # Rough token estimate
        
        metrics = {
            'generation_time': generation_time,
            'text_length': text_length,
            'tokens_per_second': tokens_per_second,
            'memory_usage': self._get_memory_usage(),
            'cuda_memory': self._get_cuda_memory_usage()
        }
        
        return metrics
    
    def _update_performance_metrics(self, generation_time: float):
        """Update running performance metrics"""
        self.performance_metrics['total_generations'] += 1
        self.performance_metrics['total_time'] += generation_time
        self.performance_metrics['average_response_time'] = (
            self.performance_metrics['total_time'] / 
            self.performance_metrics['total_generations']
        )
        self.performance_metrics['memory_usage'] = self._get_memory_usage()
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _get_cuda_memory_usage(self) -> dict:
        """Get CUDA memory usage information"""
        if not torch.cuda.is_available():
            return {'allocated': 0, 'cached': 0}
        
        return {
            'allocated': torch.cuda.memory_allocated() / 1024 / 1024,  # MB
            'cached': torch.cuda.memory_reserved() / 1024 / 1024       # MB
        }
    
    def get_performance_metrics(self) -> dict:
        """Return current performance metrics"""
        return {
            **self.performance_metrics,
            'target_response_time': 0.5,
            'actual_vs_target': f"{self.performance_metrics['average_response_time']:.3f}s vs 0.5s target",
            'performance_status': self._get_performance_status(),
            'cuda_available': torch.cuda.is_available(),
            'device': self.device
        }
    
    def _get_performance_status(self) -> str:
        """Determine performance status vs targets"""
        avg_time = self.performance_metrics['average_response_time']
        
        if avg_time <= 0.5:
            return "🏆 Excellent - Meeting target"
        elif avg_time <= 0.7:
            return "✅ Good - Close to target"
        elif avg_time <= 1.0:
            return "⚠️ Acceptable - Room for improvement"
        else:
            return "❌ Needs optimization"
    
    def cleanup_memory(self):
        """Clean up GPU memory"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        logger.debug("Memory cleanup completed")
    
    def batch_generate(self, prompts: list[str], **kwargs) -> list[tuple[str, dict]]:
        """Generate responses for multiple prompts efficiently"""
        results = []
        
        for prompt in prompts:
            result = asyncio.run(self.generate_text(prompt, **kwargs))
            results.append(result)
        
        return results
