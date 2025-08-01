"""
Event handlers for the Telegram bot - adapted for webhook deployment
"""

import logging
import os
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Rate limiting storage
user_message_counts = defaultdict(list)

# Target channel ID for Baccarat Kouamé
TARGET_CHANNEL_ID = -1002682552255

# Configuration constants
GREETING_MESSAGE = """
🎭 Salut ! Je suis le bot de Joker !
Ajoutez-moi à votre canal pour que je puisse saluer tout le monde ! 👋

🔮 Je peux analyser les combinaisons de cartes et faire des prédictions !
Utilisez /help pour voir toutes mes commandes.
"""

WELCOME_MESSAGE = """
🎭 Bienvenue dans le monde de Joker ! 

🎯 Commandes disponibles :
/start - Accueil
/help - Aide détaillée  
/about - À propos du bot
/dev - Informations développeur
/deploy - Obtenir le fichier de déploiement

🔮 Fonctionnalités spéciales :
- Prédictions de cartes automatiques
- Analyse des combinaisons
- Gestion des canaux et groupes
"""

HELP_MESSAGE = """
🎯 Guide d'utilisation du Bot Joker :

📝 Commandes de base :
/start - Message d'accueil
/help - Afficher cette aide
/about - Informations sur le bot
/dev - Contact développeur

🔮 Fonctionnalités avancées :
- Le bot analyse automatiquement les messages contenant des combinaisons de cartes
- Il fait des prédictions basées sur les patterns détectés
- Gestion intelligente des messages édités
- Support des canaux et groupes

🎴 Format des cartes :
Le bot reconnaît les symboles : ♠️ ♥️ ♦️ ♣️

📊 Le bot peut traiter les messages avec format #nXXX pour identifier les jeux.
"""

ABOUT_MESSAGE = """
🎭 Bot Joker - Prédicteur de Cartes

🤖 Version : 2.0
🛠️ Développé avec Python et l'API Telegram
🔮 Spécialisé dans l'analyse de combinaisons de cartes

✨ Fonctionnalités :
- Prédictions automatiques
- Analyse de patterns
- Support multi-canaux
- Interface intuitive

🌟 Créé pour améliorer votre expérience de jeu !
"""

DEV_MESSAGE = """
👨‍💻 Informations Développeur :

🔧 Technologies utilisées :
- Python 3.11+
- API Telegram Bot
- Flask pour les webhooks
- Déployé sur Render.com

📧 Contact : 
Pour le support technique ou les suggestions d'amélioration, 
contactez l'administrateur du bot.

🚀 Le bot est open source et peut être déployé facilement !
"""

MAX_MESSAGES_PER_MINUTE = 30
RATE_LIMIT_WINDOW = 60

def is_rate_limited(user_id: int) -> bool:
    """Check if user is rate limited"""
    now = datetime.now()
    user_messages = user_message_counts[user_id]

    # Remove old messages outside the window
    user_messages[:] = [msg_time for msg_time in user_messages 
                       if now - msg_time < timedelta(seconds=RATE_LIMIT_WINDOW)]

    # Check if user exceeded limit
    if len(user_messages) >= MAX_MESSAGES_PER_MINUTE:
        return True

    # Add current message time
    user_messages.append(now)
    return False

class TelegramHandlers:
    """Handlers for Telegram bot using webhook approach"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.deployment_file_path = "deployment.zip"
        # Import card_predictor locally to avoid circular imports
        try:
            from card_predictor import card_predictor
            self.card_predictor = card_predictor
        except ImportError:
            logger.error("Failed to import card_predictor")
            self.card_predictor = None
        
    def handle_update(self, update: Dict[str, Any]) -> None:
        """Handle incoming Telegram update with enhanced webhook support"""
        try:
            if 'message' in update:
                message = update['message']
                logger.info(f"🔄 Handlers - Traitement message normal")
                self._handle_message(message)
            elif 'edited_message' in update:
                message = update['edited_message']
                logger.info(f"🔄 Handlers - Traitement message édité pour prédictions/vérifications")
                self._handle_edited_message(message)
            else:
                logger.info(f"⚠️ Type d'update non géré: {list(update.keys())}")
                
        except Exception as e:
            logger.error(f"Error handling update: {e}")
                def _handle_edited_message(self, message: Dict[str, Any]) -> None:
        """Handle edited messages with enhanced webhook processing for predictions and verification"""
        try:
            chat_id = message['chat']['id']
            chat_type = message['chat'].get('type', 'private')
            user_id = message.get('from', {}).get('id')
            message_id = message.get('message_id')
            sender_chat = message.get('sender_chat', {})
            sender_chat_id = sender_chat.get('id')
            
            logger.info(f"✏️ WEBHOOK - Message édité reçu ID:{message_id} | Chat:{chat_id} | Sender:{sender_chat_id}")
            
            # Rate limiting check (skip for channels/groups)
            if user_id and chat_type == 'private' and is_rate_limited(user_id):
                return
            
            # Process edited messages
            if 'text' in message:
                text = message['text']
                logger.info(f"✏️ WEBHOOK - Contenu édité: {text[:100]}...")
                
                # Skip card prediction if card_predictor is not available
                if not self.card_predictor:
                    logger.warning("❌ Card predictor not available")
                    return
                
                # Vérifier que c'est du canal autorisé
                if sender_chat_id != TARGET_CHANNEL_ID:
                    logger.info(f"🚫 Message édité ignoré - Canal non autorisé: {sender_chat_id}")
                    return
                
                logger.info(f"✅ WEBHOOK - Message édité du canal autorisé: {TARGET_CHANNEL_ID}")
                
                # TRAITEMENT MESSAGES ÉDITÉS - Les deux systèmes fonctionnent ici
                if self.card_predictor.has_completion_indicators(text):
                    logger.info(f"🎯 ÉDITION - Message finalisé détecté, traitement des deux systèmes")
                    
                    # SYSTÈME 1: PRÉDICTION AUTOMATIQUE (SEULEMENT sur messages édités)
                    should_predict, game_number, combination = self.card_predictor.should_predict(text)
                    
                    if should_predict and game_number is not None and combination is not None:
                        prediction = self.card_predictor.make_prediction(game_number, combination)
                        logger.info(f"🔮 PRÉDICTION depuis ÉDITION: {prediction}")
                        
                        # Envoyer la prédiction et stocker pour futures vérifications
                        sent_message_info = self.send_message(chat_id, prediction)
                        if sent_message_info and isinstance(sent_message_info, dict) and 'message_id' in sent_message_info:
                            next_game = game_number + 1
                            self.card_predictor.sent_predictions[next_game] = {
                                'chat_id': chat_id,
                                'message_id': sent_message_info['message_id']
                            }
                            logger.info(f"📝 Prédiction stockée pour jeu {next_game}")
                    
                    # SYSTÈME 2: VÉRIFICATION (SEULEMENT sur messages édités)
                    verification_result = self.card_predictor.verify_prediction_from_edit(text)
                    if verification_result:
                        logger.info(f"🔍 VÉRIFICATION depuis ÉDITION: {verification_result}")
                        if verification_result['type'] == 'update_message':
                            # Essayer d'éditer le message original de prédiction
                            predicted_game = verification_result['predicted_game']
                            if predicted_game in self.card_predictor.sent_predictions:
                                message_info = self.card_predictor.sent_predictions[predicted_game]
                                edit_success = self.edit_message(
                                    message_info['chat_id'],
                                    message_info['message_id'],
                                    verification_result['new_message']
                                )
                                if edit_success:
                                    logger.info(f"✅ Message de prédiction édité pour jeu {predicted_game}")
                                else:
                                    self.send_message(chat_id, verification_result['new_message'])
                            else:
                                self.send_message(chat_id, verification_result['new_message'])
