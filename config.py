"""
Configuration settings for Telegram bot on Render.com
"""
import os
import logging

logger = logging.getLogger(__name__)

class Config:
    """Configuration class optimized for Render.com deployment"""
    
    def __init__(self):
        self.BOT_TOKEN = self._get_bot_token()
        self.WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
        self.PORT = self._get_clean_port()
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
        
        self._validate_config()
    
    def _get_bot_token(self) -> str:
        token = os.getenv('BOT_TOKEN', os.getenv('TELEGRAM_BOT_TOKEN', ''))
        if not token:
            logger.error("Bot token not found in environment variables")
            raise ValueError(
                "Bot token is required. Set BOT_TOKEN or TELEGRAM_BOT_TOKEN environment variable."
            )
        return token

    def _get_clean_port(self) -> int:
        """Sanitize the PORT variable to avoid conversion errors"""
        raw_port = os.getenv('PORT', '10000')
        try:
            port_str = raw_port.split()[0]  # Take only the number part
            return int(port_str)
        except ValueError:
            logger.error(f"Invalid PORT value: {raw_port}")
            raise ValueError(f"Cannot convert PORT value to integer: {raw_port}")
    
    def _validate_config(self) -> None:
        if not self.BOT_TOKEN:
            raise ValueError("Bot token is required")
        if len(self.BOT_TOKEN.split(':')) != 2:
            raise ValueError("Invalid bot token format")
        if self.WEBHOOK_URL and not self.WEBHOOK_URL.startswith('https://'):
            logger.warning("Webhook URL should use HTTPS for production")
        logger.info("Configuration validated successfully")
    
    def get_webhook_url(self) -> str:
        if self.WEBHOOK_URL:
            return f"{self.WEBHOOK_URL}/webhook"
        return ""
    
    def __str__(self) -> str:
        return f"Config(webhook_url={self.WEBHOOK_URL}, port={self.PORT}, debug={self.DEBUG})"
