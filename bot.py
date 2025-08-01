"""
Telegram Bot implementation with rate limiting and webhook support
Optimized for Render.com deployment with automatic predictions
"""
import os
import logging
import requests
import json
import time
from typing import Dict, Any
from handlers import TelegramHandlers

logger = logging.getLogger(__name__)

class TelegramBot:
    """Main Telegram bot class with advanced features"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        # Initialize handlers for message processing
        self.handlers = TelegramHandlers(token)

    def handle_update(self, update: Dict[str, Any]) -> None:
        """Handle incoming Telegram update via webhook"""
        try:
            if 'message' in update:
                logger.info("🔄 Bot traite message normal via webhook")
            elif 'edited_message' in update:
                logger.info("🔄 Bot traite message édité via webhook")
            
            # Use handlers for processing (includes card predictions)
            self.handlers.handle_update(update)
            
        except Exception as e:
            logger.error(f"❌ Error handling update: {e}")

    def send_message(self, chat_id: int, text: str) -> bool:
        """Send text message with rate limiting protection"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get('ok'):
                logger.info(f"Message sent successfully to chat {chat_id}")
                return True
            else:
                # Handle rate limiting error with automatic retry
                if result.get('error_code') == 429:
                    retry_after = result.get('parameters', {}).get('retry_after', 1)
                    logger.warning(f"Rate limited. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after + 1)
                    # Retry once after waiting
                    response = requests.post(url, json=data, timeout=10)
                    result = response.json()
                    if result.get('ok'):
                        logger.info(f"Message sent successfully after retry")
                        return True
                
                logger.error(f"Failed to send message: {result}")
                return False

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    def set_webhook(self, webhook_url: str) -> bool:
        """Set webhook URL for the bot"""
        try:
            url = f"{self.base_url}/setWebhook"
            data = {
                'url': webhook_url,
                'allowed_updates': ['message', 'edited_message']
            }

            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get('ok'):
                logger.info(f"Webhook set successfully: {webhook_url}")
                return True
            else:
                logger.error(f"Failed to set webhook: {result}")
                return False

        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False

    def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=30)
            result = response.json()

            if result.get('ok'):
                return result.get('result', {})
            else:
                logger.error(f"Failed to get bot info: {result}")
                return {}

        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return {}