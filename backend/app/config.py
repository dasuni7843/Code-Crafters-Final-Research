"""Application configuration — paths and constants."""
from pathlib import Path

# backend/ directory (parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent

MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "training" / "results"

# Frontend origins allowed to call the API
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]

APP_TITLE = "Sri Lanka Tourism AI System"
APP_VERSION = "1.0.0"

# The 20 supported destinations (canonical order from the trained encoders)
DESTINATIONS = [
    "Adams Peak", "Anuradhapura", "Arugam Bay", "Bentota", "Colombo",
    "Dambulla", "Ella", "Galle Fort", "Horton Plains", "Jaffna",
    "Kandy", "Mirissa", "Negombo", "Nuwara Eliya", "Pinnawala",
    "Polonnaruwa", "Sigiriya", "Trincomalee", "Unawatuna", "Yala",
]

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
