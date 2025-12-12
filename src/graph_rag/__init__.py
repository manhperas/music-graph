def __getattr__(name):
    if name == 'GraphRAGRetriever':
        from .retriever import GraphRAGRetriever
        return GraphRAGRetriever
    elif name == 'CypherQueryGenerator':
        from .cypher_gen import CypherQueryGenerator
        return CypherQueryGenerator
    elif name == 'PathRanker':
        from .path_ranker import PathRanker
        return PathRanker
    elif name == 'ContextBuilder':
        from .context_builder import ContextBuilder
        return ContextBuilder
    elif name == 'TripleVerbalizer':
        from .verbalizer import TripleVerbalizer
        return TripleVerbalizer
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
__all__ = ['GraphRAGRetriever', 'CypherQueryGenerator', 'PathRanker', 'ContextBuilder', 'TripleVerbalizer']
