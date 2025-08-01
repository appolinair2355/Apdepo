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
    
    def should_predict(self, message: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        SYSTÈME DE PRÉDICTION - Détermine si on doit faire une NOUVELLE prédiction (+1)
        Returns: (should_predict, game_number, card_combination)
        """
        # Extract game number
        game_number = self.extract_game_number(message)
        if not game_number:
            return False, None, None
        
        logger.debug(f"🔮 PRÉDICTION - Analyse du jeu {game_number}")
        
        # Check if this is a temporary message (should wait for final edit)
        if self.has_pending_indicators(message) and not self.has_completion_indicators(message):
            logger.info(f"🔮 Jeu {game_number}: Message temporaire (⏰▶🕐➡️), attente finalisation")
            self.temporary_messages[game_number] = message
            return False, None, None
            
        # Skip if we already have a prediction for this exact next game number
        next_game = game_number + 1
        if next_game in self.predictions and self.predictions[next_game].get('status') == 'pending':
            logger.info(f"🔮 Jeu {game_number}: Prédiction N{next_game} déjà existante, éviter doublon")
            return False, None, None
        
        # Check if this is a final message (has completion indicators)
        if self.has_completion_indicators(message):
            logger.info(f"🔮 Jeu {game_number}: Message final détecté (✅ ou 🔰)")
            # Remove from temporary if it was there
            if game_number in self.temporary_messages:
                del self.temporary_messages[game_number]
                logger.info(f"🔮 Jeu {game_number}: Retiré des messages temporaires")
        
        # Si le message a encore des indicateurs d'attente, ne pas traiter
        elif self.has_pending_indicators(message):
            logger.info(f"🔮 Jeu {game_number}: Encore des indicateurs d'attente, pas de prédiction")
            return False, None, None
        
        # Extract card symbols from each parentheses section
        parentheses_sections = self.extract_card_symbols_from_parentheses(message)
        if not parentheses_sections:
            logger.info(f"🔮 Jeu {game_number}: Aucune parenthèse trouvée")
            return False, None, None
        
        # SYSTÈME DE PRÉDICTION: Check if ANY parentheses section has exactly 3 different costumes
        # Optimisation : vérification rapide pour éviter trop de logs
        for i, section_symbols in enumerate(parentheses_sections):
            if len(section_symbols) == 3:
                # Found a section with 3 different costumes - GENERATE PREDICTION FOR NEXT GAME
                combination = ''.join(sorted(section_symbols))
                logger.info(f"🔮 PRÉDICTION - Jeu {game_number}: ✅ 3 costumes trouvés dans parenthèse {i+1}: {section_symbols}")
                logger.info(f"🔮 RÈGLE PRÉDICTION RESPECTÉE: N'importe quelle parenthèse avec 3 costumes → génère prédiction pour jeu {game_number + 1}")
                
                # Prevent duplicate processing avec optimisation
                message_hash = hash(message)
                if message_hash not in self.processed_messages:
                    self.processed_messages.add(message_hash)
                    logger.info(f"🔮 PRÉDICTION - Jeu {game_number}: GÉNÉRATION RAPIDE")
                    return True, game_number, combination
                else:
                    logger.info(f"🔮 PRÉDICTION - Jeu {game_number}: ⚠️ Déjà traité")
                    return False, None, None
            else:
                logger.info(f"🔮 PRÉDICTION - Jeu {game_number}: Parenthèse {i+1} a {len(section_symbols)} costumes: {section_symbols}")
        
        logger.info(f"🔮 PRÉDICTION - Jeu {game_number}: RÈGLE NON RESPECTÉE - Aucune parenthèse avec 3 costumes. Sections: {parentheses_sections}")
        return False, None, None
    
    def make_prediction(self, game_number: int, combination: str) -> str:
        """Make a prediction for the next game"""
        next_game = game_number + 1
        prediction_text = PREDICTION_MESSAGE.format(numero=next_game)
        
        # Store the prediction for later verification
        self.predictions[next_game] = {
            'combination': combination,
            'status': 'pending',
            'predicted_from': game_number,
            'verification_count': 0,
            'message_text': prediction_text
        }
        
        logger.info(f"Made prediction for game {next_game} based on combination {combination}")
        return prediction_text
    
    def count_cards_in_winning_parentheses(self, message: str) -> int:
        """Count the number of card symbols in the parentheses that has the ✅ symbol"""
        # Split message at ✅ to find which section won
        if '✅' not in message:
            return 0
            
        # Find the parentheses after ✅
        checkmark_pos = message.find('✅')
        remaining_text = message[checkmark_pos:]
        
        # Extract parentheses content after ✅
        pattern = r'\(([^)]+)\)'
        match = re.search(pattern, remaining_text)
        
        if match:
            winning_content = match.group(1)
            # Normalize ❤️ to ♥️ for consistent counting
            normalized_content = winning_content.replace("❤️", "♥️")
            card_count = 0
            for symbol in ["♠️", "♥️", "♦️", "♣️"]:
                card_count += normalized_content.count(symbol)
            logger.info(f"Found ✅ winning section: {winning_content}, card count: {card_count}")
            return card_count
        
        return 0
    
    def count_cards_in_first_parentheses(self, message: str) -> int:
        """Count the total number of card symbols in the first parentheses"""
        # Find first parentheses content
        pattern = r'\(([^)]+)\)'
        match = re.search(pattern, message)
        
        if match:
            first_content = match.group(1)
            # Normalize ❤️ to ♥️ for consistent counting
            normalized_content = first_content.replace("❤️", "♥️")
            card_count = 0
            for symbol in ["♠️", "♥️", "♦️", "♣️"]:
                card_count += normalized_content.count(symbol)
            logger.info(f"Found first parentheses: {first_content}, card count: {card_count}")
            return card_count
        
        return 0
    
    def verify_prediction(self, message: str) -> Optional[Dict]:
        """Verify if a prediction was correct (regular messages)"""
        return self._verify_prediction_common(message, is_edited=False)
    
    def verify_prediction_from_edit(self, message: str) -> Optional[Dict]:
        """Verify if a prediction was correct from edited message (enhanced verification)"""
        return self._verify_prediction_common(message, is_edited=True)
    
    def _verify_prediction_common(self, message: str, is_edited: bool = False) -> Optional[Dict]:
        """Common verification logic - ONLY VERIFIES on EDITED messages, checks FIRST parentheses only"""
        game_number = self.extract_game_number(message)
        if not game_number:
            return None
        
        logger.info(f"🔍 VÉRIFICATION SEULEMENT - Jeu {game_number} (édité: {is_edited})")
        
        # Vérifier TOUTES les prédictions en attente, priorité au jeu exact puis séquentiellement
        predictions_to_check = []
        
        # Synchroniser sent_predictions avec predictions
        for predicted_game, message_info in self.sent_predictions.items():
            if predicted_game not in self.predictions:
                self.predictions[predicted_game] = {
                    'status': 'pending',
                    'message_info': message_info
                }
            predictions_to_check.append(predicted_game)
        
        # Ajouter prédictions existantes
        for predicted_game in self.predictions.keys():
            if predicted_game not in predictions_to_check:
                predictions_to_check.append(predicted_game)
        
        # Trier par ordre de priorité : jeu exact d'abord, puis séquentiel
        predictions_to_check = sorted(predictions_to_check)
        
        # VÉRIFICATION SÉQUENTIELLE - Continue jusqu'à trouver une correspondance
        for predicted_game in predictions_to_check:
            prediction = self.predictions.get(predicted_game, {})
            prediction_status = prediction.get('status', 'pending')
            
            # Passer les prédictions déjà traitées
            if prediction_status != 'pending':
                continue
                
            verification_offset = game_number - predicted_game
            logger.info(f"🔍 Vérification prédiction {predicted_game} vs jeu actuel {game_number}, décalage: {verification_offset}")
            
            # VÉRIFICATION DANS LA FENÊTRE 0-3 (jeu exact, +1, +2, +3)
            if 0 <= verification_offset <= 3:
                has_success_symbol = '✅' in message or '🔰' in message
                logger.info(f"🔍 VÉRIFICATION - Jeu {game_number}: Symbole succès: {has_success_symbol}, Édité: {is_edited}")
                logger.info(f"🔍 SYSTÈME DE VÉRIFICATION: Vérifie si jeu prédit {predicted_game} correspond au jeu actuel {game_number}")
                
                # SYSTÈME DE VÉRIFICATION: SEULEMENT sur messages édités avec symbole succès
                if has_success_symbol and is_edited:
                    # RÈGLE CRITIQUE: Vérifier UNIQUEMENT le PREMIER parenthèse pour exactement 3 CARTES TOTALES (peu importe si identiques ou différentes)
                    first_parentheses_card_count = self.count_cards_in_first_parentheses(message)
                    first_parentheses_valid = first_parentheses_card_count == 3
                    
                    logger.info(f"🔍 PREMIER parenthèse: {first_parentheses_card_count} cartes au total")
                    
                    if first_parentheses_valid:
                        # Succès trouvé - déterminer le statut selon le décalage
                        status_map = {0: '✅0️⃣', 1: '✅1️⃣', 2: '✅2️⃣', 3: '✅3️⃣'}
                        new_status = status_map[verification_offset]
                        
                        logger.info(f"🔍 ✅ VÉRIFICATION RÉUSSIE - PREMIER parenthèse a exactement 3 cartes")
                        logger.info(f"🔍 RÈGLE VÉRIFICATION RESPECTÉE: Prédiction {predicted_game} trouvée au jeu {game_number} (décalage {verification_offset}) → {new_status}")
                        
                        original_message = f"🔵{predicted_game} 🔵3K: statut :⏳"
                        updated_message = f"🔵{predicted_game} 🔵3K: statut :{new_status}"
                        
                        prediction['status'] = 'correct'
                        prediction['verification_count'] = verification_offset
                        prediction['final_message'] = updated_message
                        
                        logger.info(f"🔍 ✅ Prédiction {predicted_game} VÉRIFIÉE avec succès (décalage {verification_offset})")
                        logger.info(f"🔍 📝 Message à mettre à jour: '{original_message}' → '{updated_message}'")
                        logger.info(f"🔍 🛑 ARRÊT de vérification - Succès trouvé pour prédiction {predicted_game}")
                        
                        return {
                            'type': 'update_message',
                            'predicted_game': predicted_game,
                            'new_message': updated_message,
                            'original_message': original_message
                        }
                    else:
                        # Premier parenthèse n'a pas 3 cartes - continuer à vérifier jeux suivants  
                        logger.info(f"🔍 ⏳ CONTINUE - PREMIER parenthèse a seulement {first_parentheses_card_count} cartes (besoin de 3)")
                        logger.info(f"🔍 SYSTÈME DE VÉRIFICATION: Prédiction {predicted_game} continue vers jeu suivant")
                else:
                    # Pas de symbole de succès ou pas édité - pas de vérification
                    logger.info(f"🔍 ⏸️ Pas de vérification - Symbole succès: {has_success_symbol}, Édité: {is_edited}")
            
            # Vérifier si on doit marquer comme échec après 4 jeux
            elif verification_offset >= 4:
                # Après 4 jeux (0,1,2,3) sans succès, marquer comme échec
                original_message = f"🔵{predicted_game} 🔵3K: statut :⏳"
                updated_message = f"🔵{predicted_game} 🔵3K: statut :⭕⭕"
                
                prediction['status'] = 'failed'
                prediction['final_message'] = updated_message
                
                logger.info(f"🔍 ❌ Prédiction {predicted_game} ÉCHOUÉE - Aucun succès trouvé après 4 jeux (décalages 0-3)")
                logger.info(f"🔍 🛑 ARRÊT de vérification - Échec confirmé pour prédiction {predicted_game}")
                return {
                    'type': 'update_message',
                    'predicted_game': predicted_game,
                    'new_message': updated_message,
                    'original_message': original_message
                }
        
        logger.info(f"🔍 Aucune prédiction à vérifier pour le jeu {game_number}")
        return None

# Global instance
card_predictor = CardPredictor()ctor()
