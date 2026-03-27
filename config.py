import os
from dotenv import load_dotenv

load_dotenv()

# Search Settings
DEFAULT_NUM_RESULTS = 10

# Extraction Settings
EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

# Groq API (free LLM for result classification)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Gmail SMTP (for bulk email sending)
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
