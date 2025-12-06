"""
API module for Music Knowledge Graph Chatbot.

Provides:
- FastAPI server for REST API
- Gradio UI for interactive chat
"""

from .server import app, create_app
from .gradio_app import create_gradio_interface

__all__ = ['app', 'create_app', 'create_gradio_interface']





