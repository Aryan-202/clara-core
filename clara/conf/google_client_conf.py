"""
This module contains all the required settings regarding google client configurations
"""

import os

from dotenv import load_dotenv

load_dotenv()

AUTH_URI = os.getenv("AUTH_URI")

SCOPES = ['https://googleapis.com']
