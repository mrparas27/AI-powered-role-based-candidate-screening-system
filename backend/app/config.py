import os
from dotenv import load_dotenv

# Load env variables from root or backend folder
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/database.sqlite")

# Ensure the database data directory exists
os.makedirs("./data", exist_ok=True)
