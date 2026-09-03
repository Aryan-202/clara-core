"""
Google OAuth 2.0 Handler for Clara backend.

This module handles the Google OAuth flow for multiple client types:
- Web applications (with client secret)
- Desktop applications (public client with localhost callback)
- Mobile applications (public client with custom URI scheme)
"""

import json
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qs

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow

from clara.conf.settings import settings


class GoogleOAuthHandler:
    """
    Handles Google OAuth 2.0 for multiple client types.
    
    This class provides methods for:
    1. Generating authorization URLs for different platforms
    2. Exchanging authorization codes for tokens
    3. Refreshing expired tokens
    4. Getting user information from Google
    """
    
    def __init__(self):
        self.client_id_web = settings.GOOGLE_CLIENT_ID_WEB
        self.client_secret_web = settings.GOOGLE_CLIENT_SECRET_WEB
        self.scopes = settings.GOOGLE_SCOPES
        
    def get_authorization_url(
        self,
        platform: str = 'web',
        state: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate Google OAuth authorization URL for a specific platform.
        
        Args:
            platform: 'web', 'desktop', 'android', or 'ios'
            state: Optional state parameter for CSRF protection
            redirect_uri: Optional custom redirect URI
            
        Returns:
            Dictionary with authorization URL and state
        """
        if not state:
            import secrets
            state = secrets.token_urlsafe(32)
        
        # Determine client ID and redirect URI based on platform
        if platform == 'web':
            client_id = self.client_id_web
            redirect_uri = redirect_uri or settings.REDIRECT_URI_WEB
            response_type = 'code'
        elif platform == 'desktop':
            client_id = settings.GOOGLE_CLIENT_ID_DESKTOP
            redirect_uri = redirect_uri or settings.REDIRECT_URI_DESKTOP
            response_type = 'code'
        elif platform in ['android', 'ios']:
            client_id = (
                settings.GOOGLE_CLIENT_ID_ANDROID 
                if platform == 'android' 
                else settings.GOOGLE_CLIENT_ID_IOS
            )
            redirect_uri = redirect_uri or settings.REDIRECT_URI_MOBILE
            response_type = 'code'
        else:
            raise ValueError(f'Unsupported platform: {platform}')
        
        # Build authorization URL
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': response_type,
            'scope': ' '.join(self.scopes),
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state,
        }
        
        # Add PKCE for public clients (mobile/desktop)
        if platform in ['desktop', 'android', 'ios']:
            import hashlib
            import base64
            
            code_verifier = secrets.token_urlsafe(64)
            code_challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).decode().rstrip('=')
            
            params['code_challenge_method'] = 'S256'
            params['code_challenge'] = code_challenge
            
            # Store code_verifier for later use
            # In production, store this in a session or temporary cache
            self._store_code_verifier(state, code_verifier)
        
        url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
        
        return {
            'url': url,
            'state': state,
            'platform': platform,
        }
    
    def exchange_code_for_tokens(
        self,
        code: str,
        platform: str = 'web',
        redirect_uri: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Exchange authorization code for access and refresh tokens.
        
        This is the critical step that happens on the backend.
        The client sends the authorization code, and the backend
        exchanges it using the client secret (for web apps) or
        without (for public clients with PKCE).
        
        Args:
            code: Authorization code from Google
            platform: 'web', 'desktop', 'android', or 'ios'
            redirect_uri: Redirect URI used in the original request
            state: State parameter for verification
            
        Returns:
            Dictionary with access_token, refresh_token, and id_token
        """
        # Determine redirect URI based on platform
        if platform == 'web':
            redirect_uri = redirect_uri or settings.REDIRECT_URI_WEB
            # Web apps use client secret
            token_url = 'https://oauth2.googleapis.com/token'
            data = {
                'code': code,
                'client_id': self.client_id_web,
                'client_secret': self.client_secret_web,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            }
            
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
        
        elif platform == 'desktop':
            redirect_uri = redirect_uri or settings.REDIRECT_URI_DESKTOP
            # Desktop apps use PKCE - no client secret
            flow = InstalledAppFlow.from_client_config(
                client_config={
                    'installed': {
                        'client_id': settings.GOOGLE_CLIENT_ID_DESKTOP,
                        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                        'token_uri': 'https://oauth2.googleapis.com/token',
                        'redirect_uris': [redirect_uri],
                    }
                },
                scopes=self.scopes,
            )
            
            # Exchange code using the flow
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            return {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'id_token': credentials.id_token,
                'expires_in': 3600,
            }
        
        elif platform in ['android', 'ios']:
            redirect_uri = redirect_uri or settings.REDIRECT_URI_MOBILE
            # Mobile apps use PKCE - no client secret
            # Similar to desktop but with mobile client ID
            client_id = (
                settings.GOOGLE_CLIENT_ID_ANDROID 
                if platform == 'android' 
                else settings.GOOGLE_CLIENT_ID_IOS
            )
            
            # Use the code verifier stored earlier
            code_verifier = self._get_code_verifier(state) if state else None
            
            token_url = 'https://oauth2.googleapis.com/token'
            data = {
                'code': code,
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            }
            
            if code_verifier:
                data['code_verifier'] = code_verifier
            
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
        
        else:
            raise ValueError(f'Unsupported platform: {platform}')
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh an expired access token using the refresh token.
        
        Args:
            refresh_token: The refresh token obtained during initial auth
            
        Returns:
            Dictionary with new access_token and expiry
        """
        token_url = 'https://oauth2.googleapis.com/token'
        data = {
            'client_id': self.client_id_web,
            'client_secret': self.client_secret_web,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict[str, str]:
        """
        Get user information from Google using access token.
        
        Args:
            access_token: Valid access token
            
        Returns:
            User info (email, name, picture, etc.)
        """
        url = 'https://www.googleapis.com/oauth2/v3/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def _store_code_verifier(self, state: str, code_verifier: str) -> None:
        """Store code verifier for PKCE flow."""
        # In production, use Redis or a database cache
        # This is a simple in-memory store for demonstration
        if not hasattr(self, '_code_verifiers'):
            self._code_verifiers = {}
        self._code_verifiers[state] = code_verifier
    
    def _get_code_verifier(self, state: str) -> Optional[str]:
        """Retrieve code verifier for PKCE flow."""
        if hasattr(self, '_code_verifiers'):
            return self._code_verifiers.get(state)
        return None