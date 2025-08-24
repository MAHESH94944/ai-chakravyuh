from core.clients import tavily_client
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def tavily_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Performs a resilient web search using the Tavily API with automatic retries.

    Args:
        query: The search query string.
        max_results: The maximum number of results to return.
    
    Returns:
        A list of search results.
    """
    try:
        print(f"    -> Performing Tavily search for: '{query}'")
        response = tavily_client.search(query=query, search_depth="basic", max_results=max_results)
        return response.get("results", [])
    except Exception as e:
        print(f"An error occurred during Tavily search for query '{query}': {e}")
        # Reraise the exception to trigger tenacity's retry mechanism
        raise