import os
from dotenv import load_dotenv

# Load .env file from project root
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(dotenv_path=env_path)

COHERE_API_KEY = os.getenv("COHERE_API_KEY", "").strip()
if COHERE_API_KEY:
    print("[Config] Loaded COHERE_API_KEY from .env successfully.")
else:
    print("[Config] COHERE_API_KEY not found in .env (Running in local offline fallback mode).")
