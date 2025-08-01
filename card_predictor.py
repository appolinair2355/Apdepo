"""
Card prediction logic for Joker's Telegram Bot - simplified for webhook deployment
"""

import re
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
import os

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
        self.predictions = {}
        self.processed_messages = set()
        self.sent_predictions = {}
        self.temporary_messages = {}
        self.pending_edits = {}
    
    def reset_predictions(self):
        self.predictions.clear()
        self.processed_messages.clear()
        self.sent_predictions.clear()
        self.temporary_messages.clear()
        self.pending_edits.clear()
        logger.info("🔄 Système de prédictions réinitialisé")
    
    def extract_game_number(self, message: str) -> Optional[int]:
        pattern = r'#[nN](\d+)'
        match = re.search(pattern, message)
        return int(match.group(1)) if match else None
    
    def extract_cards_from_parentheses(self, message: str) -> List[str]:
        return []
    
    def has_pending_indicators(self, text: str) -> bool:
        indicators = ['⏰', '▶', '🕐', '➡️']
        return any(indicator in text for indicator in indicators)
    
    def has_completion_indicators(self, text: str) -> bool:
        completion_indicators = ['✅', '🔰']
        return any(indicator in text for indicator in completion_indicators)
    
    def should_wait_for_edit(self, text: str, message_id: int) -> bool:
        if self.has_pending_indicators(text):
            self.pending_edits[message_id] = {
                'original_text': text,
                'timestamp': datetime.now()
            }
            return True
        return False
    
    def extract_card_symbols_from_parentheses(self, text: str) -> List[List[str]]:
        pattern = r'\(([^)]+)\)'
        matches = re.findall(pattern, text)
        
        all_sections = []
        for match in matches:
            normalized_content = match.replace("❤️", "♥️")
            unique_symbols = {s for s in ["♠️", "♥️", "♦️", "♣️"] if s in normalized_content}
            all_sections.append(list(unique_symbols))
        
        return all_sections
    
    def has_three_different_cards(self, cards: List[str]) -> bool:
        unique_cards = list(set(cards))
        logger.info(f"Checking cards: {cards}, unique: {unique_cards}, count: {len(unique_cards)}")
        return len(unique_cards) == 3
    
    def is_temporary_message(self, message: str) -> bool:
        temporary_emojis = ['⏰', '▶', '🕐', '➡️']
        return any(emoji in message for emoji in temporary_emojis)
    
    def is_final_message(self, message: str) -> bool:
        final_emojis = ['✅', '🔰']
        return any(emoji in message for emoji in final_emojis)
    
    def get_card_combination(self, cards: List[str]) -> Optional[str]:
        unique_cards = list(set(cards))
        if len(unique_cards) == 3:
            combination = ''.join(sorted(unique_cards))
            logger.info(f"Card combination found: {combination} from cards: {unique_cards}")
            for valid_combo in VALID_CARD_COMBINATIONS:
                if set(combination) == set(valid_combo):
                    logger.info(f"Valid combination matched: {valid_combo}")
                    return combination
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
        
        if user_id and chat_type == 'private' and is_rate_limited(user_id):
            return
        
        if 'text' in message:
            text = message['text']
            logger.info(f"✏️ WEBHOOK - Contenu édité: {text[:100]}...")
            
            if not self.card_predictor:
                logger.warning("❌ Card predictor not available")
                return
            
            if sender_chat_id != TARGET_CHANNEL_ID:
                logger.info(f"🚫 Message édité ignoré - Canal non autorisé: {sender_chat_id}")
                return
            
            logger.info(f"✅ WEBHOOK - Message édité du canal autorisé: {TARGET_CHANNEL_ID}")
            
            if self.card_predictor.has_completion_indicators(text):
                logger.info(f"🎯 ÉDITION - Message finalisé détecté, traitement des deux systèmes")
                
                should_predict, game_number, combination = self.card_predictor.should_predict(text)
                if should_predict and game_number is not None and combination is not None:
                    prediction = self.card_predictor.make_prediction(game_number, combination)
                    logger.info(f"🔮 PRÉDICTION depuis ÉDITION: {prediction}")
                    sent_message_info = self.send_message(chat_id, prediction)
                    if sent_message_info and isinstance(sent_message_info, dict) and 'message_id' in sent_message_info:
                        next_game = game_number + 1
                        self.card_predictor.sent_predictions[next_game] = {
                            'chat_id': chat_id,
                            'message_id': sent_message_info['message_id']
                        }
                        logger.info(f"📝 Prédiction stockée pour jeu {next_game}")
                
                verification_result = self.card_predictor.verify_prediction_from_edit(text)
                if verification_result:
                    logger.info(f"🔍 VÉRIFICATION depuis ÉDITION: {verification_result}")
                    if verification_result['type'] == 'update_message':
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
            
            elif self.card_predictor.has_pending_indicators(text):
                logger.info(f"⏰ WEBHOOK - Message temporaire détecté, en attente de finalisation")
                if message_id:
                    self.card_predictor.pending_edits[message_id] = {
                        'original_text': text,
                        'timestamp': datetime.now()
                    }
    except Exception as e:
        logger.error(f"❌ Error handling edited message via webhook: {e}")
