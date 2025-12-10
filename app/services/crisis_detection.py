"""
Crisis Detection Model - Stanford CMD-1 Inspired Two-Stage Detection

This module implements a crisis detection system based on academic research
into crisis language detection. The model uses a two-stage approach:

Stage 1: Fast keyword filtering to identify potentially concerning messages
Stage 2: Feature extraction and probability scoring using 20 core features

Feature Categories (20 total):
1. Crisis keyword count - Direct crisis language mentions
2. First-person pronoun ratio - Self-referential language patterns  
3. Negative sentiment score - Overall emotional valence
4. Future tense indicators - Planning or intent markers
5. Hopelessness markers - Language indicating despair
6. Isolation language - Social disconnection indicators
7. Planning language - Specific intent or method references
8. Finality language - Goodbye/ending expressions
9. Burden language - Self-perception as a burden
10. Question vs statement ratio - Communication style
11. Message length - Very short or very long messages
12. Absolute words - All-or-nothing thinking patterns
13. Help-seeking language - Requests for assistance
14. Past trauma mentions - Historical distress references
15. Medication/treatment mentions - Healthcare context
16. Social connection mentions - Support network presence (protective)
17. Coping mechanisms - Active coping strategies (protective)
18. Time markers - Urgency indicators
19. Certainty markers - Decisiveness in language
20. Ambivalence markers - Mixed feelings (protective)

Scoring: Features are weighted based on risk severity, with crisis keywords
receiving highest weight. Protective factors reduce the overall score.
"""
import re
from typing import Dict, Any, List


class CrisisDetectionModel:
    
    def __init__(self):
        self.crisis_keywords = [
            'kill myself', 'end my life', 'want to die',
            'suicide', 'suicidal', 'self harm', 'self-harm',
            'cut myself', 'hurt myself', 'no point',
            'better off dead', "can't go on", 'end it all',
            'take my life', 'not worth living', 'wish i was dead',
            'rather be dead', 'life is meaningless', 'give up on life'
        ]
        
        self.hopelessness_markers = [
            'no point', "can't", 'never', 'hopeless', 'worthless',
            'pointless', 'nothing matters', 'why bother', 'give up'
        ]
        
        self.isolation_markers = [
            'alone', 'nobody', 'no one', 'lonely', 'abandoned',
            'isolated', 'left me', 'no friends', "don't care"
        ]
        
        self.planning_markers = [
            'how to', 'will', 'going to', 'plan to', 'decided to',
            'method', 'way to', 'pills', 'gun', 'bridge', 'jump'
        ]
        
        self.finality_markers = [
            'goodbye', 'last', 'end', 'final', 'forever',
            'never again', 'last time', 'one last'
        ]
        
        self.burden_markers = [
            'burden', 'better without', 'weighing down',
            'drag on', "they'd be happier"
        ]
        
        self.first_person_pronouns = ['i', 'me', 'my', 'myself', 'mine']
        self.absolute_words = ['always', 'never', 'everyone', 'nobody', 'nothing', 'everything']
        self.help_seeking = ['help', 'need', 'please', 'someone']
        self.time_markers = ['today', 'tonight', 'soon', 'now', 'tomorrow']
        self.certainty_markers = ['will', 'going to', 'definitely', 'decided']
        self.ambivalence_markers = ['but', 'maybe', "i don't know", 'not sure', 'part of me']
    
    def detect(self, user_message: str) -> Dict[str, Any]:
        if not self.has_crisis_keywords(user_message):
            return {
                'crisis_detected': False,
                'confidence': 0.0,
                'stage': 1
            }
        
        features = self.extract_features(user_message)
        probability = self.calculate_probability(features)
        
        return {
            'crisis_detected': probability >= 0.5,
            'confidence': probability,
            'stage': 2,
            'features': features
        }
    
    def has_crisis_keywords(self, text: str) -> bool:
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.crisis_keywords)
    
    def extract_features(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        words = text_lower.split()
        word_count = len(words)
        
        features = {
            'crisis_keyword_count': self._count_keywords(text_lower, self.crisis_keywords),
            'first_person_ratio': self._calculate_ratio(words, self.first_person_pronouns),
            'negative_sentiment': self._sentiment_score(text_lower),
            'future_tense_present': self._has_future_tense(text_lower),
            'hopelessness_markers': self._count_keywords(text_lower, self.hopelessness_markers),
            'isolation_language': self._count_keywords(text_lower, self.isolation_markers),
            'planning_language': self._count_keywords(text_lower, self.planning_markers),
            'finality_language': self._count_keywords(text_lower, self.finality_markers),
            'burden_language': self._count_keywords(text_lower, self.burden_markers),
            'question_ratio': self._question_ratio(text),
            'message_length': word_count,
            'absolute_words': self._count_keywords(text_lower, self.absolute_words),
            'help_seeking_language': self._count_keywords(text_lower, self.help_seeking),
            'past_trauma_mentions': self._check_trauma_mentions(text_lower),
            'medication_mentions': self._check_medication_mentions(text_lower),
            'social_connection_mentions': self._check_social_mentions(text_lower),
            'coping_mechanisms': self._check_coping_mentions(text_lower),
            'time_markers': self._count_keywords(text_lower, self.time_markers),
            'certainty_markers': self._count_keywords(text_lower, self.certainty_markers),
            'ambivalence_markers': self._count_keywords(text_lower, self.ambivalence_markers),
        }
        
        return features
    
    def calculate_probability(self, features: Dict[str, Any]) -> float:
        score = 0.0
        
        crisis_count = features['crisis_keyword_count']
        if crisis_count >= 1:
            score += 0.40
        if crisis_count >= 2:
            score += 0.20
        
        score += min(features['hopelessness_markers'] * 0.10, 0.20)
        score += min(features['isolation_language'] * 0.08, 0.16)
        score += min(features['planning_language'] * 0.15, 0.30)
        score += min(features['finality_language'] * 0.12, 0.24)
        score += min(features['burden_language'] * 0.10, 0.20)
        
        if features['first_person_ratio'] > 0.10:
            score += 0.05
        
        if features['negative_sentiment'] > 0.3:
            score += features['negative_sentiment'] * 0.15
        
        if features['future_tense_present']:
            score += 0.05
        
        if features['certainty_markers'] > 0:
            score += 0.08
        
        if features['ambivalence_markers'] > 0:
            score -= 0.02
        
        if features['help_seeking_language'] > 0:
            score += 0.02
        
        if features['social_connection_mentions'] > 0:
            score -= 0.03
        
        if features['coping_mechanisms'] > 0:
            score -= 0.03
        
        return min(max(score, 0.0), 1.0)
    
    def _count_keywords(self, text: str, keywords: List[str]) -> int:
        return sum(1 for keyword in keywords if keyword in text)
    
    def _calculate_ratio(self, words: List[str], target_words: List[str]) -> float:
        if not words:
            return 0.0
        count = sum(1 for word in words if word in target_words)
        return count / len(words)
    
    def _sentiment_score(self, text: str) -> float:
        negative_words = [
            'sad', 'depressed', 'hopeless', 'worthless', 'terrible',
            'awful', 'horrible', 'miserable', 'pain', 'hurt', 'hate',
            'angry', 'frustrated', 'anxious', 'scared', 'afraid',
            'tired', 'exhausted', 'empty', 'numb', 'broken'
        ]
        
        positive_words = [
            'happy', 'good', 'great', 'wonderful', 'love', 'hope',
            'excited', 'grateful', 'thankful', 'better', 'improved'
        ]
        
        neg_count = self._count_keywords(text, negative_words)
        pos_count = self._count_keywords(text, positive_words)
        
        total = neg_count + pos_count
        if total == 0:
            return 0.3
        
        return neg_count / total
    
    def _has_future_tense(self, text: str) -> bool:
        future_patterns = [
            r'\bwill\b', r'\bgoing to\b', r"'ll\b", r'\bgonna\b'
        ]
        return any(re.search(pattern, text) for pattern in future_patterns)
    
    def _question_ratio(self, text: str) -> float:
        sentences = re.split(r'[.!?]+', text)
        if not sentences:
            return 0.0
        questions = sum(1 for s in sentences if '?' in s)
        return questions / len(sentences)
    
    def _check_trauma_mentions(self, text: str) -> int:
        trauma_words = ['abuse', 'trauma', 'assault', 'violence', 'accident']
        return self._count_keywords(text, trauma_words)
    
    def _check_medication_mentions(self, text: str) -> int:
        med_words = ['medication', 'pills', 'prescription', 'therapy', 'therapist', 'doctor']
        return self._count_keywords(text, med_words)
    
    def _check_social_mentions(self, text: str) -> int:
        social_words = ['friend', 'family', 'mom', 'dad', 'sister', 'brother', 'partner']
        return self._count_keywords(text, social_words)
    
    def _check_coping_mentions(self, text: str) -> int:
        coping_words = ['exercise', 'walk', 'music', 'hobby', 'breathe', 'relax', 'meditation']
        return self._count_keywords(text, coping_words)


crisis_detector = CrisisDetectionModel()
