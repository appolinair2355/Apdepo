"""
Card prediction logic for Joker's Telegram Bot - simplified for webhook deployment
"""

import re
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)

# Configuration constants
VALID_CARD_COMBINATIONS = [
    "♠️♥️♦️", "♠️♥️♣️", "♠️♦️♣️", "♥️♦️♣️"
]

CARD_SYMBOLS = ["♠️", "♥️", "♦️", "♣️", "❤️"]  # Include both ♥️ and ❤️ variants

PREDICTION_MESSAGE = "🔵{numero} 🔵3K: statut :⏳"

class CardPredictor:
    """Handles card prediction logic for webhook deployment"""
    
    def __init__(self):
        self.predictions = {}  # Store predictions for verification
        self.processed_messages = set()  # Avoid duplicate processing
        self.sent_predictions = {}  # Store sent prediction messages for editing
        self.temporary_messages = {}  # Store temporary messages waiting for final edit
        self.pending_edits = {}  # Store messages waiting for edit with indicators
        
    def reset_predictions(self):
        """Reset all prediction states - useful for recalibration"""
        self.predictions.clear()
        self.processed_messages.clear()
        self.sent_predictions.clear()
        self.temporary_messages.clear()
        self.pending_edits.clear()
        logger.info("🔄 Système de prédictions réinitialisé")
    
    def extract_game_number(self, message: str) -> Optional[int]:
        """Extract game number from message like #n744 or #N744"""
        pattern = r'#[nN](\d+)'
        match = re.search(pattern, message)
        if match:
            return int(match.group(1))
        return None
    
    def extract_cards_from_parentheses(self, message: str) -> List[str]:
        """Extract cards from first and second parentheses"""
        # This method is deprecated, use extract_card_symbols_from_parentheses instead
        return []
    
    def has_pending_indicators(self, text: str) -> bool:
        """Check if message contains indicators suggesting it will be edited"""
        indicators = ['⏰', '▶', '🕐', '➡️']
        return any(indicator in text for indicator in indicators)
    
    def has_completion_indicators(self, text: str) -> bool:
        """Check if message contains completion indicators after edit"""
        completion_indicators = ['✅', '🔰']
        return any(indicator in text for indicator in completion_indicators)
    
    def should_wait_for_edit(self, text: str, message_id: int) -> bool:
        """Determine if we should wait for this message to be edited"""
        if self.has_pending_indicators(text):
            # Store this message as pending edit
            self.pending_edits[message_id] = {
                'original_text': text,
                'timestamp': datetime.now()
            }
            return True
        return False
    
    def extract_card_symbols_from_parentheses(self, text: str) -> List[List[str]]:
        """Extract unique card symbols from each parentheses section"""
        # Find all parentheses content
        pattern = r'\(([^)]+)\)'
        matches = re.findall(pattern, text)
        
        all_sections = []
        for match in matches:
            # Normalize ❤️ to ♥️ for consistency
            normalized_content = match.replace("❤️", "♥️")
            
            # Extract only unique card symbols (costumes) from this section
            unique_symbols = set()
            for symbol in ["♠️", "♥️", "♦️", "♣️"]:
                if symbol in normalized_content:
                    unique_symbols.add(symbol)
            
            all_sections.append(list(unique_symbols))
        
        return all_sections
    
    def has_three_different_cards(self, cards: List[str]) -> bool:
        """Check if there are exactly 3 different card symbols"""
        unique_cards = list(set(cards))
        logger.info(f"Checking cards: {cards}, unique: {unique_cards}, count: {len(unique_cards)}")
        return len(unique_cards) == 3
    
    def is_temporary_message(self, message: str) -> bool:
        """Check if message contains temporary progress emojis"""
        temporary_emojis = ['⏰', '▶', '🕐', '➡️']
        return any(emoji in message for emoji in temporary_emojis)
    
    def is_final_message(self, message: str) -> bool:
        """Check if message contains final completion emojis"""
        final_emojis = ['✅', '🔰']
        return any(emoji in message for emoji in final_emojis)
    
    def get_card_combination(self, cards: List[str]) -> Optional[str]:
        """Get the combination of 3 different cards"""
        unique_cards = list(set(cards))
        if len(unique_cards) == 3:
            combination = ''.join(sorted(unique_cards))
            logger.info(f"Card combination found: {combination} from cards: {unique_cards}")
            
            # Check if this combination matches any valid pattern
            for valid_combo in VALID_CARD_COMBINATIONS:
                if set(combination) == set(valid_combo):
                    logger.info(f"Valid combination matched: {valid_combo}")
                    return combination
            
            # Accept any 3 different cards as valid
            logger.info(f"Accepting 3 different cards as valid: {combination}")
            return combination
        return None
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
                
                # Gestion des messages temporaires
                elif self.card_predictor.has_pending_indicators(text):
                    logger.info(f"⏰ WEBHOOK - Message temporaire détecté, en attente de finalisation")
                    if message_id:
                        self.card_predictor.pending_edits[message_id] = {
                            'original_text': text,
                            'timestamp': datetime.now()
                        }
                
        except Exception as e:
            logger.error(f"❌ Error handling edited message via webhook: {e}")
    
    def _process_card_message(self, message: Dict[str, Any]) -> None:
        """Process message for card prediction (works for both regular and edited messages)"""
        try:
            chat_id = message['chat']['id']
            text = message.get('text', '')
            sender_chat = message.get('sender_chat', {})
            sender_chat_id = sender_chat.get('id')
            
            # Only process messages from Baccarat Kouamé channel
            if sender_chat_id != TARGET_CHANNEL_ID:
                logger.info(f"🚫 Message ignoré - Canal non autorisé: {sender_chat_id} (attendu: {TARGET_CHANNEL_ID})")
                return
                
            if not text or not self.card_predictor:
                return
                
            logger.info(f"🎯 Traitement message CANAL AUTORISÉ pour prédiction: {text[:50]}...")
            logger.info(f"📍 Canal source: {sender_chat_id} | Chat destination: {chat_id}")
            
            # IMPORTANT: Les messages normaux ne font PAS de prédiction ni de vérification
            # Seuls les messages ÉDITÉS déclenchent les systèmes de prédiction et vérification
            logger.info(f"📨 Message normal - AUCUNE ACTION (prédiction et vérification se font SEULEMENT sur messages édités)")
            
            # Store temporary messages with pending indicators
            if self.card_predictor.has_pending_indicators(text):
                message_id = message.get('message_id')
                if message_id:
                    self.card_predictor.temporary_messages[message_id] = text
                    logger.info(f"⏰ Message temporaire stocké: {message_id}")
                
        except Exception as e:
            logger.error(f"Error processing card message: {e}")
    
    def _process_completed_edit(self, message: Dict[str, Any]) -> None:
        """Process a message that was edited and now contains completion indicators"""
        try:
            chat_id = message['chat']['id']
            chat_type = message['chat'].get('type', 'private')
            text = message['text']
            
            # Only process in groups/channels
            if chat_type in ['group', 'supergroup', 'channel'] and self.card_predictor:
                # Check if we should make a prediction from this completed edit
                should_predict, game_number, combination = self.card_predictor.should_predict(text)
                
                if should_predict and game_number is not None and combination is not None:
                    prediction = self.card_predictor.make_prediction(game_number, combination)
                    logger.info(f"Making prediction from completed edit: {prediction}")
                    
                    # Send prediction to the chat
                    self.send_message(chat_id, prediction)
                
                # Also check for verification with enhanced logic for edited messages
                verification_result = self.card_predictor.verify_prediction_from_edit(text)
                if verification_result:
                    logger.info(f"Verification from completed edit: {verification_result}")
                    
                    if verification_result['type'] == 'update_message':
                        self.send_message(chat_id, verification_result['new_message'])
                        
        except Exception as e:
            logger.error(f"Error processing completed edit: {e}")
    
    def _handle_start_command(self, chat_id: int) -> None:
        """Handle /start command"""
        try:
            self.send_message(chat_id, WELCOME_MESSAGE)
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            self.send_message(chat_id, "❌ Une erreur s'est produite. Veuillez réessayer.")
    
    def _handle_deploy_command(self, chat_id: int) -> None:
        """Handle /deploy command by sending deployment zip file"""
        try:
            # Send initial message
            self.send_message(
                chat_id, 
                "🚀 Préparation du fichier de déploiement... Veuillez patienter."
            )
            
            # Check if deployment file exists
            if not os.path.exists(self.deployment_file_path):
                self.send_message(
                    chat_id,
                    "❌ Fichier de déploiement non trouvé. Contactez l'administrateur."
                )
                logger.error(f"Deployment file {self.deployment_file_path} not found")
                return
            
            # Send the file
            success = self.send_document(chat_id, self.deployment_file_path)
            
            if success:
                self.send_message(
                    chat_id,
                    "✅ Fichier de déploiement envoyé avec succès !\n\n"
                    "📋 Instructions de déploiement :\n"
                    "1. Téléchargez le fichier zip\n"
                    "2. Créez un nouveau service sur render.com\n"
                    "3. Uploadez le zip ou connectez votre repository\n"
                    "4. Configurez les variables d'environnement :\n"
                    "   - BOT_TOKEN : Votre token de bot\n"
                    "   - WEBHOOK_URL : https://votre-app.onrender.com\n"
                    "   - PORT : 10000\n\n"
                    "🎯 Votre bot sera déployé automatiquement !"
                )
            else:
                self.send_message(
                    chat_id,
                    "❌ Échec de l'envoi du fichier. Réessayez plus tard."
                )
                
        except Exception as e:
            logger.error(f"Error handling deploy command: {e}")
            self.send_message(
                chat_id,
                "❌ Une erreur s'est produite lors du traitement de votre demande."
            )
    
    def _handle_regular_message(self, message: Dict[str, Any]) -> None:
        """Handle regular text messages"""
        try:
            chat_id = message['chat']['id']
            chat_type = message['chat'].get('type', 'private')
            text = message.get('text', '')
            message_id = message.get('message_id')
            
            # In private chats, provide help
            if chat_type == 'private':
                self.send_message(
                    chat_id,
                    "🎭 Salut ! Je suis le bot de Joker.\n"
                    "Utilisez /help pour voir mes commandes disponibles.\n\n"
                    "Ajoutez-moi à un canal pour que je puisse analyser les cartes ! 🎴"
                )
            
            # In groups/channels, analyze for card patterns
            elif chat_type in ['group', 'supergroup', 'channel'] and self.card_predictor:
                # Check if this message has pending indicators
                if message_id and self.card_predictor.should_wait_for_edit(text, message_id):
                    logger.info(f"Message {message_id} has pending indicators, waiting for edit: {text[:50]}...")
                    # Don't process for predictions yet, wait for the edit
                    return
                
                # Les messages normaux dans les groupes/canaux ne font PAS de prédiction ni vérification
                # Seuls les messages ÉDITÉS déclenchent les systèmes
                logger.info(f"📨 Message normal groupe/canal - AUCUNE ACTION (systèmes actifs seulement sur éditions)")
                logger.info(f"Group message in {chat_id}: {text[:50]}...")
                
        except Exception as e:
            logger.error(f"Error handling regular message: {e}")
    
    def _handle_new_chat_members(self, message: Dict[str, Any]) -> None:
        """Handle when bot is added to a channel or group"""
        try:
            chat_id = message['chat']['id']
            chat_title = message['chat'].get('title', 'ce chat')
            
            for member in message['new_chat_members']:
                # Check if our bot was added (we can't know our own ID easily in webhook mode)
                # So we'll just send greeting when any bot is added
                if member.get('is_bot', False):
                    logger.info(f"Bot added to chat {chat_id}: {chat_title}")
                    self.send_message(chat_id, GREETING_MESSAGE)
                    break
                    
        except Exception as e:
            logger.error(f"Error handling new chat members: {e}")
    
    def send_message(self, chat_id: int, text: str) -> bool:
        """Send text message to user"""
        try:
            import requests
            
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
                return result.get('result', {})  # Return message info including message_id
            else:
                logger.error(f"Failed to send message: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def send_document(self, chat_id: int, file_path: str) -> bool:
        """Send document file to user"""
        try:
            import requests
            
            url = f"{self.base_url}/sendDocument"
            
            with open(file_path, 'rb') as file:
                files = {
                    'document': (os.path.basename(file_path), file, 'application/zip')
                }
                data = {
                    'chat_id': chat_id,
                    'caption': '📦 Package de déploiement pour render.com\n\n🎯 Tout est inclus pour déployer votre bot !'
                }
                
                response = requests.post(url, data=data, files=files, timeout=60)
                result = response.json()
                
                if result.get('ok'):
                    logger.info(f"Document sent successfully to chat {chat_id}")
                    return True
                else:
                    logger.error(f"Failed to send document: {result}")
                    return False
                    
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Error sending document: {e}")
            return False
    
    def edit_message(self, chat_id: int, message_id: int, new_text: str) -> bool:
        """Edit an existing message"""
        try:
            import requests
            
            url = f"{self.base_url}/editMessageText"
            data = {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': new_text,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                logger.info(f"Message edited successfully in chat {chat_id}")
                return True
            else:
                logger.error(f"Failed to edit message: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            return False
