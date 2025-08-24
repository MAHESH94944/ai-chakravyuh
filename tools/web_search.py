from core.clients import tavily_client


def tavily_search(query: str, max_results: int = 10, **kwargs) -> list[dict]:
    """
    Performs a web search using the Tavily API.

    This wrapper accepts a flexible set of parameters and attempts to map
    the common `max_results` argument to the concrete parameter name used by
    the installed Tavily client (which may be `max_results`, `limit`, or `count`).

    Args:
        query: The search query string.
        max_results: Preferred number of results to return per query.
        **kwargs: Additional provider-specific keyword arguments.

    Returns:
        A list of search results (each result is a dict). On error returns an empty list.
    """
    # Prepare the base params
    base_params = {"query": query, "search_depth": kwargs.pop("search_depth", "basic")}

    # Try several common parameter names for limiting results
    candidate_names = ["max_results", "limit", "count", "n"]
    tried = []

    for name in candidate_names:
        params = base_params.copy()
        params[name] = max_results
        params.update(kwargs)
        try:
            response = tavily_client.search(**params)
            # If the client returned something, try to extract results
            if isinstance(response, dict):
                return response.get("results", []) or response.get("items", []) or []
            # If it returned a list directly
            if isinstance(response, list):
                return response
        except TypeError as e:
            # The client didn't accept this parameter name; try the next one
            tried.append((name, str(e)))
            continue
        except Exception as e:
            print(f"An error occurred during Tavily search (param {name}): {e}")
            return []

    # Final attempt: call with only base params
    try:
        response = tavily_client.search(**base_params)
        if isinstance(response, dict):
            return response.get("results", []) or response.get("items", []) or []
        if isinstance(response, list):
            return response
    except Exception as e:
        print(f"Tavily search failed after trying params {tried}: {e}")

    return []