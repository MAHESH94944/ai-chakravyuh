import google.generativeai as genai
from groq import Groq
from tavily import TavilyClient
from .config import settings

# Configure the Gemini client with the API key from our settings
genai.configure(api_key=settings.GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# Configure the Groq client
groq_client = Groq(api_key=settings.GROQ_API_KEY)

# Configure the Tavily client
tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)