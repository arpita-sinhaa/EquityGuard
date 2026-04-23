import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")
TABLE = os.getenv("TABLE")

FULL_TABLE = f"{PROJECT_ID}.{DATASET}.{TABLE}"