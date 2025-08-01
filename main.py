"""
Main entry point for Telegram bot deployment on Render.com
Optimized for webhook-based communication with automatic predictions
"""
import os
import logging
from flask import Flask, request
from bot import TelegramBot
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize bot configuration and instance
config = Config()
bot = TelegramBot(config.BOT_TOKEN)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from Telegram"""
    try:
        update = request.get_json()
        
        if 'message' in update:
            logger.info("📨 Webhook - Message normal reçu")
        elif 'edited_message' in update:
            logger.info("✏️ Webhook - Message édité reçu")
        
        if update:
            bot.handle_update(update)
            logger.info("✅ Update traité avec succès via webhook")
        
        return 'OK', 200
    except Exception as e:
        logger.error(f"❌ Error handling webhook: {e}")
        return 'Error', 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render.com"""
    return {'status': 'healthy', 'service': 'telegram-bot'}, 200

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return {'message': 'Telegram Bot is running', 'status': 'active'}, 200

def setup_webhook():
    """Set up webhook on startup for Render.com deployment"""
    try:
        webhook_url = config.WEBHOOK_URL
        if webhook_url and webhook_url.strip():
            full_webhook_url = f"{webhook_url}/webhook"
            logger.info(f"🔗 Configuration webhook pour Render.com: {full_webhook_url}")
            
            success = bot.set_webhook(full_webhook_url)
            if success:
                logger.info(f"✅ Webhook configuré avec succès sur Render.com")
                logger.info(f"🎯 Bot prêt pour prédictions automatiques")
            else:
                logger.error("❌ Échec configuration webhook")
        else:
            logger.warning("⚠️ WEBHOOK_URL non configurée pour Render.com")
    except Exception as e:
        logger.error(f"❌ Erreur configuration webhook: {e}")

if __name__ == '__main__':
    # Set up webhook on startup
    setup_webhook()
    
    # Get port from environment (Render.com provides this dynamically)
    port = int(os.getenv('PORT', 10000))
    logger.info(f"🚀 Démarrage serveur sur port {port}")
    
    # Run Flask app optimized for Render.com
    app.run(host='0.0.0.0', port=port, debug=False)