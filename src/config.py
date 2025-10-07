import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
REPORTS_DIR = BASE_DIR / "reports"

LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "bot.log"