"""
Prompt generation utilities for chat nodes.
Extracted to maintain PocketFlow 150-line Node limit.
"""


def build_context_prompt(query: str, search_results: list) -> str:
    """Build prompt with context from search results"""
    # Build context sections
    context_sections = []
    for i, result in enumerate(search_results[:5]):
        if result.get('content'):
            context_sections.append(f"[Source {i+1}]: {result['content']}")
    
    if not context_sections:
        return f"""You are a helpful theological AI assistant. A user has asked: "{query}"

However, I don't have any specific document content to reference for this question. Please provide a helpful response based on your general knowledge, but note that you don't have access to specific documents at this time.

Question: {query}

Please provide a thoughtful response and indicate that more specific sources would be helpful for a more detailed answer."""
    
    context_text = "\n\n".join(context_sections)
    return f"""You are a helpful theological AI assistant. Please answer the user's question based on the provided document sources.

Context from relevant documents:
{context_text}

User's Question: {query}

Please provide a comprehensive answer based on the context provided. If the context doesn't fully address the question, indicate what aspects might need additional sources. When referencing information, please cite the source number (e.g., [Source 1]).

Answer:"""


def build_hermeneutics_prompt(hermeneutics_rules: str, context_chunks: list, query: str) -> str:
    """Compose hermeneutics-guided prompt: [Rules] + [Context] + [Query]"""
    context_text = format_context_chunks(context_chunks)
    
    return "\n".join([
        "=== HERMENEUTICAL FRAMEWORK ===", hermeneutics_rules, "",
        "=== RELEVANT SOURCE MATERIAL ===", context_text, "",
        "=== USER QUESTION ===", query, "",
        "=== INSTRUCTIONS ===",
        "Using the hermeneutical framework above and the provided source material, "
        "provide a comprehensive, biblically grounded response to the user's question. "
        "Cite specific biblical references and maintain theological precision."
    ])


def format_context_chunks(chunks: list) -> str:
    """Format document chunks for prompt inclusion"""
    if not chunks:
        return "No relevant source material found."
    
    formatted_chunks = []
    for i, chunk in enumerate(chunks[:5], 1):
        content = chunk.get('content', '')[:1000]
        title = chunk.get('title', 'Unknown Source')
        citation = chunk.get('citation', '')
        chunk_text = f"Source {i}: {title}\n{content}"
        if citation:
            chunk_text += f"\nCitation: {citation}"
        formatted_chunks.append(chunk_text)
    
    return "\n\n".join(formatted_chunks)


def build_source_info(search_results: list) -> list:
    """Build source information from search results"""
    source_info = []
    for i, result in enumerate(search_results[:5]):
        if result.get('content'):
            source_info.append({
                "source_number": i+1,
                "citation": result.get('citation', f"Source {i+1}"),
                "relevance": result.get('relevance', 0.0),
                "document_id": result.get('document_id'),
                "title": result.get('title', 'Unknown Document')
            })
    return source_info