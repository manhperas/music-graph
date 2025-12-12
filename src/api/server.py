import os
import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's question or message")
    context: Optional[str] = Field(None, description='Optional context from graph')
    use_graph: bool = Field(True, description='Whether to use GraphRAG for context')
    max_hops: int = Field(2, description='Maximum hops for graph traversal')

    class Config:
        json_schema_extra = {'example': {'message': 'What genre does Taylor Swift play?', 'use_graph': True, 'max_hops': 2}}

class ChatResponse(BaseModel):
    answer: str = Field(..., description='Generated answer')
    context: Optional[str] = Field(None, description='Graph context used')
    entities: List[str] = Field(default_factory=list, description='Entities found')
    paths_count: int = Field(0, description='Number of graph paths found')
    processing_time: float = Field(..., description='Processing time in seconds')

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    neo4j_connected: bool
    timestamp: str

class GraphQueryRequest(BaseModel):
    entity: str = Field(..., description='Entity name to search')
    max_hops: int = Field(2, description='Maximum hops from entity')

class GraphQueryResponse(BaseModel):
    entity: str
    connections: List[Dict[str, Any]]
    total_connections: int

class AppState:

    def __init__(self):
        self.chatbot = None
        self.graph_retriever = None
        self.neo4j_driver = None
        self.model_loaded = False
        self.neo4j_connected = False

    def initialize(self, lora_path: Optional[str]=None, use_neo4j: bool=False):
        try:
            from src.models.qwen_model import Qwen3MusicChatbot
            self.chatbot = Qwen3MusicChatbot(model_name='Qwen/Qwen3-0.6B', lora_path=lora_path, quantization='4bit', max_new_tokens=256, temperature=0.1)
            self.model_loaded = True
            logger.info('✅ Chatbot model loaded successfully')
        except Exception as e:
            logger.warning(f'⚠️ Could not load chatbot model: {e}')
            self.model_loaded = False
        if use_neo4j:
            try:
                from neo4j import GraphDatabase
                from src.graph_rag import GraphRAGRetriever
                neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
                neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
                neo4j_pass = os.getenv('NEO4J_PASS', 'password')
                self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
                with self.neo4j_driver.session() as session:
                    session.run('RETURN 1')
                self.graph_retriever = GraphRAGRetriever(self.neo4j_driver)
                self.neo4j_connected = True
                logger.info('✅ Neo4j connected successfully')
            except Exception as e:
                logger.warning(f'⚠️ Could not connect to Neo4j: {e}')
                self.neo4j_connected = False

    def cleanup(self):
        if self.neo4j_driver:
            self.neo4j_driver.close()
            logger.info('Neo4j connection closed')
app_state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('🚀 Starting Music Knowledge Graph Chatbot API...')
    lora_path = os.getenv('LORA_PATH', 'models/qwen3-music-lora')
    use_neo4j = os.getenv('USE_NEO4J', 'false').lower() == 'true'
    app_state.initialize(lora_path=lora_path, use_neo4j=use_neo4j)
    yield
    logger.info('Shutting down...')
    app_state.cleanup()

def create_app() -> FastAPI:
    app = FastAPI(title='Music Knowledge Graph Chatbot API', description='\n        A chatbot API for answering questions about music using a knowledge graph.\n        \n        Features:\n        - Answer questions about artists, albums, songs, genres\n        - Multi-hop reasoning using GraphRAG\n        - Fine-tuned Qwen3 model with LoRA\n        ', version='1.0.0', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
    return app
app = create_app()

@app.get('/', tags=['Root'])
async def root():
    return {'name': 'Music Knowledge Graph Chatbot API', 'version': '1.0.0', 'docs_url': '/docs', 'health_url': '/health'}

@app.get('/health', response_model=HealthResponse, tags=['Health'])
async def health_check():
    return HealthResponse(status='healthy', model_loaded=app_state.model_loaded, neo4j_connected=app_state.neo4j_connected, timestamp=datetime.now().isoformat())

@app.post('/chat', response_model=ChatResponse, tags=['Chat'])
async def chat(request: ChatRequest):
    import time
    start_time = time.time()
    if not app_state.model_loaded or app_state.chatbot is None:
        answer = generate_fallback_response(request.message)
        return ChatResponse(answer=answer, context=None, entities=[], paths_count=0, processing_time=time.time() - start_time)
    try:
        context = request.context
        entities = []
        paths_count = 0
        if request.use_graph and app_state.graph_retriever:
            result = app_state.chatbot.answer_with_graph_context(request.message, app_state.graph_retriever, max_hops=request.max_hops)
            answer = result['answer']
            context = result.get('context', '')
            entities = result.get('entities', [])
            paths_count = result.get('paths_count', 0)
        else:
            answer = app_state.chatbot.generate(request.message, context=context)
        answer = re.sub('<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
        processing_time = time.time() - start_time
        return ChatResponse(answer=answer, context=context, entities=entities, paths_count=paths_count, processing_time=processing_time)
    except Exception as e:
        logger.error(f'Error in chat: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/query_graph', response_model=GraphQueryResponse, tags=['Graph'])
async def query_graph(request: GraphQueryRequest):
    if not app_state.neo4j_connected or not app_state.graph_retriever:
        raise HTTPException(status_code=503, detail='Neo4j is not connected. Enable with USE_NEO4J=true')
    try:
        connections = app_state.graph_retriever._find_entity_connections(request.entity)
        return GraphQueryResponse(entity=request.entity, connections=connections, total_connections=len(connections))
    except Exception as e:
        logger.error(f'Error querying graph: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/models/status', tags=['Models'])
async def model_status():
    return {'chatbot_loaded': app_state.model_loaded, 'neo4j_connected': app_state.neo4j_connected, 'model_name': 'Qwen/Qwen3-0.6B' if app_state.model_loaded else None, 'lora_path': os.getenv('LORA_PATH', 'models/qwen3-music-lora')}

def generate_fallback_response(message: str) -> str:
    message_lower = message.lower()
    if any((word in message_lower for word in ['hello', 'hi', 'hey'])):
        return "Hello! I'm the Music Knowledge Graph Chatbot. Ask me about artists, albums, songs, or genres!"
    if 'genre' in message_lower:
        return "I can help you with music genres! However, my main model isn't loaded right now. Please try again later."
    if any((word in message_lower for word in ['album', 'song', 'track'])):
        return "I can help you find information about albums and songs! However, my main model isn't loaded right now."
    if any((word in message_lower for word in ['artist', 'singer', 'band', 'musician'])):
        return "I can tell you about artists and bands! However, my main model isn't loaded right now."
    return "I'm the Music Knowledge Graph Chatbot. My main model isn't loaded right now, but I can help with music questions once it's ready!"
if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    logger.info(f'Starting server on {host}:{port}')
    uvicorn.run('src.api.server:app', host=host, port=port, reload=True, log_level='info')
