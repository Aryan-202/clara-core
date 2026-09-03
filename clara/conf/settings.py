"""
Configuration management for Clara backend.

Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv('.env.development')

class Settings:
    """Clara Settings"""
    GOOGLE_CLIENT_ID_WEB: str = os.getenv('GOOGLE_CLIENT_ID_WEB', '')
    GOOGLE_CLIENT_SECRET_WEB: str = os.getenv('GOOGLE_CLIENT_SECRET_WEB', '')
    
    GOOGLE_CLIENT_ID_DESKTOP: str = os.getenv('GOOGLE_CLIENT_ID_DESKTOP', '')
    
    GOOGLE_CLIENT_ID_ANDROID: str = os.getenv('GOOGLE_CLIENT_ID_ANDROID', '')
    GOOGLE_CLIENT_ID_IOS: str = os.getenv('GOOGLE_CLIENT_ID_IOS', '')
    
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', '')
    JWT_ALGORITHM: str = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_MINUTES: int = int(os.getenv('JWT_EXPIRATION_MINUTES', 60))
    REFRESH_TOKEN_EXPIRATION_DAYS: int = int(os.getenv('REFRESH_TOKEN_EXPIRATION_DAYS', 30))

    GOOGLE_SCOPES: List[str] = [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/drive.file',
    ]

    REDIRECT_URI_WEB: str = os.getenv('REDIRECT_URI_WEB', 'http://localhost:8000/auth/google/callback')
    REDIRECT_URI_DESKTOP: str = os.getenv('REDIRECT_URI_DESKTOP', 'http://localhost:8080')
    REDIRECT_URI_MOBILE: str = os.getenv('REDIRECT_URI_MOBILE', 'com.clara.app://oauth2callback')

    @classmethod
    def validate(cls) -> None:
        """Validate required settings are present."""
        if not cls.GOOGLE_CLIENT_ID_WEB or not cls.GOOGLE_CLIENT_SECRET_WEB:
            raise ValueError(
                'GOOGLE_CLIENT_ID_WEB and GOOGLE_CLIENT_SECRET_WEB must be set '
                'for backend token exchange.'
            )
        if not cls.JWT_SECRET_KEY:
            raise ValueError('JWT_SECRET_KEY must be set for JWT generation.')


settings = Settings()
settings.validate()