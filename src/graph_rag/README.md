# GraphRAG - Graph Retrieval-Augmented Generation

## Tổng Quan

GraphRAG là implementation của Graph Retrieval-Augmented Generation cho music knowledge graph chatbot. Hệ thống sử dụng Neo4j database để retrieve relevant information và cung cấp context cho language models để trả lời câu hỏi về âm nhạc.

## Cấu Trúc

```
src/graph_rag/
├── __init__.py          # Package initialization with lazy imports
├── retriever.py         # Main GraphRAGRetriever class
├── cypher_gen.py        # Cypher query generation
├── path_ranker.py       # Path ranking and filtering
├── context_builder.py   # Natural language context construction
├── verbalizer.py        # Triple verbalization
└── README.md           # This file
```

## Components

### 1. GraphRAGRetriever

**Main orchestrator** cho toàn bộ GraphRAG pipeline:

```python
from neo4j import GraphDatabase
from graph_rag import GraphRAGRetriever

driver = GraphDatabase.driver(uri, auth=(user, password))
retriever = GraphRAGRetriever(driver)

result = retriever.retrieve_context("Did Taylor Swift collaborate with Ed Sheeran?")
print(result['context_text'])
```

### 2. CypherQueryGenerator

**Tạo Cypher queries** để truy vấn Neo4j graph:

```python
from graph_rag import CypherQueryGenerator

generator = CypherQueryGenerator()

# Extract entities từ query
entities = generator.parse_entities_from_query("Did Taylor Swift win Grammy?")
# → ['Taylor Swift', 'Grammy']

# Generate path query
query = generator.generate_path_query(entities, max_hops=3)
```

### 3. PathRanker

**Rank graph paths** theo độ relevant với user query:

```python
from graph_rag import PathRanker

ranker = PathRanker()
ranked_paths = ranker.rank_paths(paths, query, entities)
```

**Scoring factors**:
- Path length (shorter = better)
- Entity match (direct connections = better)
- Relation relevance (relevant relations = better)
- Node importance (important nodes = better)

### 4. TripleVerbalizer

**Convert graph triples** thành natural language:

```python
from graph_rag import TripleVerbalizer

verbalizer = TripleVerbalizer()

triple = ('Taylor Swift', 'COLLABORATES_WITH', 'Ed Sheeran')
text = verbalizer.verbalize_triple(triple)
# → "Taylor Swift collaborated with Ed Sheeran"
```

### 5. ContextBuilder

**Build coherent context** từ ranked paths:

```python
from graph_rag import ContextBuilder

builder = ContextBuilder()
context = builder.build_context(ranked_paths, query)
```

## Pipeline

1. **Query Processing**: Extract entities từ user query
2. **Graph Retrieval**: Tìm paths trong Neo4j connecting entities
3. **Path Ranking**: Rank paths theo relevance score
4. **Context Construction**: Build natural language context
5. **LLM Integration**: Use context để generate answer

## Usage Examples

### Basic Usage

```python
import os
from neo4j import GraphDatabase
from graph_rag import GraphRAGRetriever

# Setup Neo4j connection
driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    auth=(os.getenv('NEO4J_USER', 'neo4j'),
          os.getenv('NEO4J_PASSWORD', 'password'))
)

# Initialize retriever
retriever = GraphRAGRetriever(driver)

# Ask questions
queries = [
    "Did Taylor Swift collaborate with Ed Sheeran?",
    "What awards has Billie Eilish won?",
    "What genre does The Beatles play?"
]

for query in queries:
    result = retriever.retrieve_context(query)
    print(f"Q: {query}")
    print(f"A: {result['context_text']}")
    print()
```

### Advanced Usage

```python
# Analyze query complexity
analysis = retriever.analyze_query_complexity(query)
print(f"Complexity: {analysis['complexity_level']}")
print(f"Entities: {analysis['entity_count']}")

# Get detailed entity info
entity_info = retriever.get_entity_info("Taylor Swift")
print(f"Entity labels: {entity_info['labels']}")

# Find similar entities
similar = retriever.search_similar_entities("Taylor Swift")
print(f"Similar artists: {similar}")
```

## Configuration

### Environment Variables

```bash
# Neo4j connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Optional: OpenAI API (future enhancement)
OPENAI_API_KEY=your_key_here
```

### Parameters

```python
# Initialize với custom parameters
retriever = GraphRAGRetriever(
    neo4j_driver=driver,
    llm_model=None  # Future: Qwen model instance
)

# Custom retrieval parameters
result = retriever.retrieve_context(
    query="Did Taylor Swift win Grammy?",
    max_hops=2  # Limit path length
)
```

## Testing

### Run Basic Tests

```bash
cd /path/to/music-graph
python3 scripts/test_graph_rag_basic.py
```

### Run Demo

```bash
python3 scripts/graph_rag_demo.py
```

## Dependencies

```
neo4j>=5.14.0          # Neo4j driver
transformers>=4.40.0   # For future LLM integration
torch>=2.0.0          # PyTorch for models
spacy>=3.7.0          # NLP processing
sentence-transformers>=2.2.0  # Text embeddings
```

## Error Handling

GraphRAG handles various error conditions gracefully:

- **No entities found**: Returns helpful message
- **No paths found**: Suggests similar entities
- **Database connection error**: Graceful degradation
- **Empty results**: Meaningful empty state messages

## Performance

**Target Performance**:
- Query latency: < 2 seconds
- Path finding: < 500ms for typical queries
- Context building: < 100ms

**Optimization Strategies**:
- Query result caching
- Path pruning during retrieval
- Batch processing for multiple queries
- Neo4j index utilization

## Future Enhancements

- [ ] LLM-powered entity extraction
- [ ] Conversational memory
- [ ] Multi-modal context (images, audio)
- [ ] Knowledge graph expansion
- [ ] Advanced reasoning capabilities

## Architecture Details

Chi tiết về architecture và design decisions xem tại:
`docs/technical/GRAPHRAG_CHATBOT_ARCHITECTURE.md`
