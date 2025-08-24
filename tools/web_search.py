from core.clients import tavily_client

def tavily_search(query: str) -> list[dict]:
    """
    Performs a web search using the Tavily API.

    Args:
        query: The search query string.
    
    Returns:
        A list of search results.
    """
    try:
        response = tavily_client.search(query=query, search_depth="basic")
        return response.get("results", [])
    except Exception as e:
        print(f"An error occurred during Tavily search: {e}")
        return []