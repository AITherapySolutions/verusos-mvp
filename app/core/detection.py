"""
VerusOS Detection Engine v2.2 - EXPANDED KEYWORDS
Comprehensive safety detection with expanded pattern coverage
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class DetectionResult:
    """Complete detection result"""
    crisis_detected: bool
    grooming_detected: bool
    violence_detected: bool
    
    confidence_score: float
    risk_score: int
    risk_tier: str
    
    stage: int
    categories: List[str]
    keywords_matched: List[str]
    features: Dict[str, float]
    context_multipliers: Dict[str, float]
    
    recommended_action: str
    response_deadline_hours: int

class CrisisDetector:
    """Three-category detection system with comprehensive patterns"""
    
    def __init__(self):
        # CRISIS KEYWORDS - EXPANDED
        self.crisis_keywords = [
            # Explicit suicidal ideation
            r'\b(kill|end).*(myself|my life)\b',
            r'\b(want|going|gonna).*(die|suicide|dead)\b',
            r'\bsuicid(e|al)\b',
            r'\bkill myself\b',
            r'\bend my life\b',
            r'\bend it all\b',
            r'\bwant to die\b',
            r'\bend this\b',
            r'\bending it\b',
            
            # Self-harm
            r'\b(cut|hurt|harm).*(myself|self)\b',
            r'\bself.?harm\b',
            r'\bhurt myself\b',
            r'\bcut myself\b',
            
            # Hopelessness - expanded
            r'\b(no|not).*(worth|point).*(living|anymore)\b',
            r'\b(can\'t|cannot).*(go on|take it|do this)\b',
            r'\bbetter off (dead|without me)\b',
            r'\bno point\b',
            r'\bno reason to live\b',
            r'\bworthless\b',
            r'\bhopeless\b',
            r'\b(nobody|no one).*(cares|wants|loves)\b',
            r'\beveryone.*(better off|hate)\b',
            r'\bwant to disappear\b',
            r'\bdon\'t want to (live|exist|be here)\b',
            r'\btired of living\b',
            r'\bgive up\b',
            r'\bcan\'t go on\b',
            r'\bno future\b',
            r'\bno hope\b',
            r'\bdon\'t see a future\b',
            r'\bcare if i\'m gone\b',
            r'\bwant it to stop\b',
            r'\bpain.*unbearable\b',
            r'\bunbearable\b',
            r'\bcan\'t take\b',
            
            # Planning language
            r'\b(how to|ways to).*(kill|die|suicide|end)\b',
            r'\b(pills|gun|rope|bridge|knife)\b.*\b(die|suicide|end|myself)\b',
            r'\bhave a (gun|knife|pills)\b',
            r'\bplanning.*(end|die|suicide|kill)\b',
            r'\bprepared everything\b',
            r'\bwrote.*(note|letter|goodbye)\b',
            r'\bpills\b.*\b(easy|easiest|way)\b',
            r'\bthought about ending\b',
            r'\bbeen planning\b',
            
            # Goodbye language
            r'\bgoodbye.*(world|everyone|all)\b',
            r'\bfinal goodbye\b',
            r'\bthis is (the end|it|goodbye)\b',
        ]
        
        # GROOMING KEYWORDS - EXPANDED
        self.grooming_keywords = [
            # Age/identity questions
            r'\b(how old|what age|age)\b.*\b(you|are|r u)\b',
            r'\b(what|which).*(school|grade)\b',
            r'\bwhere.*(live|from|located|stay)\b',
            r'\bwhat.*(address|location)\b',
            r'\btell me.*(name|phone|where|about yourself)\b',
            
            # Photo requests
            r'\bsend.*(picture|photo|pic|selfie|image)\b',
            r'\bshow me.*(picture|photo|yourself|you)\b',
            r'\b(can i|let me|want to).*(see|have).*(photo|picture|you)\b',
            r'\bpic of you\b',
            r'\bselfie\b',
            
            # Meetup attempts
            r'\bmeet.*(up|irl|in person|real life|sometime)\b',
            r'\b(come|go).*(meet|see).*(me|you)\b',
            r'\bpick you up\b',
            r'\bmy (car|place|house|apartment)\b',
            r'\bcome to my\b',
            r'\bcome over\b',
            r'\bhang out.*(alone|private)\b',
            
            # Secrecy/manipulation
            r'\b(don\'t tell|keep.*(secret|between|private))\b',
            r'\b(our|this).*(secret|special|private)\b',
            r'\bnobody.*(needs to|has to|should) know\b',
            r'\bjust between us\b',
            r'\bour little secret\b',
            
            # Flattery/grooming compliments
            r'\byou\'re.*(mature|pretty|hot|sexy|beautiful|cute)\b',
            r'\byou look (older|mature|hot|sexy)\b',
            r'\bso (mature|pretty|beautiful|hot)\b',
            r'\bage.*(just a number|doesn\'t matter)\b',
            r'\b(really|so) mature\b',
            r'\bmature for your age\b',
            r'\bseem.*(mature|older)\b',
        ]
        
        # VIOLENCE KEYWORDS - EXPANDED
        self.violence_keywords = [
            # Direct threats
            r'\b(kill|hurt|attack|harm).*(them|him|her|someone|people|you)\b',
            r'\bi\'m (going to|gonna|will).*(hurt|kill|attack)\b',
            r'\bgoing to (hurt|kill|attack|harm)\b',
            r'\bwant to (hurt|kill|attack|harm).*(them|him|her|someone)\b',
            r'\bthey.*(deserve|should|going to|will).*die\b',
            r'\b(make|watch).*(them|him|her).*(die|suffer|pay)\b',
            
            # Weapons + intent
            r'\b(gun|knife|weapon|bomb)\b.*\b(kill|hurt|use|shoot|stab)\b',
            r'\b(shoot|stab|blow up|attack)\b',
            r'\bhave a (gun|knife|weapon)\b',
            r'\bbring a (gun|knife|weapon)\b',
            
            # Mass violence
            r'\bshoot.*(up|school|place|everyone|them all)\b',
            r'\bmass.*(shooting|killing|murder)\b',
            r'\b(kill|hurt|attack).*(everyone|them all|all of them)\b',
            r'\bmake them (pay|suffer|regret)\b',
            r'\bthey\'ll.*(pay|regret|sorry)\b',
            
            # Specific/planned threats
            r'\bi know where.*(live|work|go|are)\b',
            r'\bi have a (list|plan|target)\b',
            r'\bplanning.*(attack|hurt|kill|shoot)\b',
            r'\bthey won\'t see.*(coming|it)\b',
            r'\bpreparing.*(attack|weapons)\b',
            r'\bplanned this\b',
            r'\bepic destruction\b',
        ]
        
        # Compile patterns
        self.crisis_patterns = [re.compile(p, re.IGNORECASE) for p in self.crisis_keywords]
        self.grooming_patterns = [re.compile(p, re.IGNORECASE) for p in self.grooming_keywords]
        self.violence_patterns = [re.compile(p, re.IGNORECASE) for p in self.violence_keywords]
    
    def detect(self, message: str, context: Optional[Dict] = None) -> DetectionResult:
        """Run detection with context"""
        context = context or {}
        
        # Stage 1: Keyword matching - count matches
        crisis_matches = self._count_matches(message, self.crisis_patterns)
        grooming_matches = self._count_matches(message, self.grooming_patterns)
        violence_matches = self._count_matches(message, self.violence_patterns)
        
        # If nothing triggered, return safe result
        if not (crisis_matches or grooming_matches or violence_matches):
            return self._safe_result()
        
        # Stage 2: Calculate scores based on keyword matches
        # Base score: 0.7 for first match, +0.1 for each additional (capped at 1.0)
        crisis_score = min(0.7 + (crisis_matches - 1) * 0.1, 1.0) if crisis_matches else 0.0
        grooming_score = min(0.7 + (grooming_matches - 1) * 0.1, 1.0) if grooming_matches else 0.0
        violence_score = min(0.7 + (violence_matches - 1) * 0.1, 1.0) if violence_matches else 0.0
        
        # Extract features for context adjustment
        features = self._extract_features(message)
        
        # Apply feature adjustments (small modifiers)
        crisis_score = self._adjust_crisis_score(crisis_score, features)
        grooming_score = self._adjust_grooming_score(grooming_score, features)
        violence_score = self._adjust_violence_score(violence_score, features)
        
        # Take highest score as primary risk
        base_score = max(crisis_score, grooming_score, violence_score)
        
        # Apply context multipliers
        multipliers = self._calc_multipliers(message, context, features)
        final_score = self._apply_multipliers(base_score, multipliers)
        
        # Normalize to 0-100
        risk_score = int(final_score * 100)
        risk_tier, action, deadline = self._assign_tier(risk_score)
        
        # Categories (threshold 0.5)
        categories = []
        if crisis_score >= 0.5: categories.append('crisis')
        if grooming_score >= 0.5: categories.append('grooming')
        if violence_score >= 0.5: categories.append('violence')
        
        keywords = self._get_keywords(message)
        
        return DetectionResult(
            crisis_detected=crisis_score >= 0.5,
            grooming_detected=grooming_score >= 0.5,
            violence_detected=violence_score >= 0.5,
            confidence_score=final_score,
            risk_score=risk_score,
            risk_tier=risk_tier,
            stage=2,
            categories=categories,
            keywords_matched=keywords,
            features=features,
            context_multipliers=multipliers,
            recommended_action=action,
            response_deadline_hours=deadline
        )
    
    def _count_matches(self, msg: str, patterns: List) -> int:
        """Count how many patterns match"""
        return sum(1 for p in patterns if p.search(msg))
    
    def _extract_features(self, msg: str) -> Dict[str, float]:
        """Extract linguistic features"""
        lower = msg.lower()
        words = lower.split()
        count = len(words) or 1
        
        first_person = ['i', 'me', 'my', 'myself', 'mine', "i'm", "i've", "i'll"]
        fp_cnt = sum(1 for w in words if w in first_person)
        
        negative = ['no', 'not', 'never', 'nothing', 'nobody', 'alone', 'empty', 'hopeless', 'worthless', 'hate', "can't", 'cannot']
        neg_cnt = sum(1 for w in words if w in negative)
        
        future = ['will', 'going', 'gonna', 'tomorrow', 'tonight', 'planning', 'plan']
        future_cnt = sum(1 for w in words if w in future)
        
        urgency = ['now', 'tonight', 'today', 'immediately', 'right now']
        urgency_cnt = sum(1 for w in words if w in urgency)
        
        questions = ['what', 'where', 'when', 'how', 'who', 'why']
        q_cnt = sum(1 for w in words if w in questions)
        
        imperatives = ['send', 'show', 'tell', 'come', 'meet', 'give', 'let']
        imp_cnt = sum(1 for w in words if w in imperatives)
        
        return {
            'first_person_count': fp_cnt,
            'negative_count': neg_cnt,
            'future_count': future_cnt,
            'urgency_count': urgency_cnt,
            'question_count': q_cnt,
            'imperative_count': imp_cnt,
            'word_count': count,
            'has_first_person': 1.0 if fp_cnt > 0 else 0.0,
            'has_negative': 1.0 if neg_cnt > 0 else 0.0,
            'has_urgency': 1.0 if urgency_cnt > 0 else 0.0,
        }
    
    def _adjust_crisis_score(self, base: float, f: Dict) -> float:
        if base == 0:
            return 0
        score = base
        if f.get('has_first_person'):
            score += 0.05
        if f.get('has_negative'):
            score += 0.05
        if f.get('has_urgency'):
            score += 0.1
        return min(score, 1.0)
    
    def _adjust_grooming_score(self, base: float, f: Dict) -> float:
        if base == 0:
            return 0
        score = base
        if f.get('question_count', 0) > 1:
            score += 0.05
        if f.get('imperative_count', 0) > 1:
            score += 0.05
        return min(score, 1.0)
    
    def _adjust_violence_score(self, base: float, f: Dict) -> float:
        if base == 0:
            return 0
        score = base
        if f.get('future_count', 0) > 0:
            score += 0.05
        if f.get('has_urgency'):
            score += 0.1
        return min(score, 1.0)
    
    def _calc_multipliers(self, msg: str, ctx: Dict, f: Dict) -> Dict[str, float]:
        mult = {}
        if not ctx:
            return mult
        time = (ctx.get('time_of_day') or '').lower()
        if any(h in time for h in ['2am', '3am', '4am', '5am', '2:00', '3:00', '4:00', '5:00']):
            mult['late_night'] = 1.3
        sessions = ctx.get('session_count_today', 0)
        if sessions > 20:
            mult['excessive_usage'] = 1.3
        elif sessions > 10:
            mult['high_usage'] = 1.2
        age = ctx.get('user_age')
        if age and age < 18:
            mult['minor_user'] = 1.3
        return mult
    
    def _apply_multipliers(self, base: float, mult: Dict) -> float:
        score = base
        for m in mult.values():
            score *= m
        return min(score, 1.0)
    
    def _assign_tier(self, score: int) -> tuple:
        if score >= 90:
            return ("CRITICAL", "Immediate intervention required", 1)
        elif score >= 70:
            return ("HIGH", "Urgent review required", 4)
        elif score >= 50:
            return ("ELEVATED", "Review within 24 hours", 24)
        else:
            return ("BASELINE", "Standard monitoring", 168)
    
    def _get_keywords(self, msg: str) -> List[str]:
        matched = []
        for i, p in enumerate(self.crisis_patterns):
            if p.search(msg):
                matched.append(f"crisis:{self.crisis_keywords[i][:30]}")
        for i, p in enumerate(self.grooming_patterns):
            if p.search(msg):
                matched.append(f"grooming:{self.grooming_keywords[i][:30]}")
        for i, p in enumerate(self.violence_patterns):
            if p.search(msg):
                matched.append(f"violence:{self.violence_keywords[i][:30]}")
        return matched[:10]
    
    def _safe_result(self) -> DetectionResult:
        return DetectionResult(
            crisis_detected=False,
            grooming_detected=False,
            violence_detected=False,
            confidence_score=0.0,
            risk_score=0,
            risk_tier="BASELINE",
            stage=1,
            categories=[],
            keywords_matched=[],
            features={},
            context_multipliers={},
            recommended_action="Continue normal conversation",
            response_deadline_hours=168
        )

# Global instance
detector = CrisisDetector()
