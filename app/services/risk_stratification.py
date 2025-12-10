from typing import Dict, Any, Optional
from datetime import datetime


class RiskStratificationEngine:
    
    TIER_THRESHOLDS = {
        1: {'min_score': 90, 'label': 'IMMEDIATE - Imminent Crisis', 'deadline_hours': 1},
        2: {'min_score': 70, 'label': 'URGENT - High Risk', 'deadline_hours': 4},
        3: {'min_score': 50, 'label': 'ELEVATED - Moderate Concern', 'deadline_hours': 24},
        4: {'min_score': 0, 'label': 'BASELINE - Low Risk', 'deadline_hours': 72},
    }
    
    LATE_NIGHT_HOURS = ['12am', '1am', '2am', '3am', '4am', '5am', '6am']
    
    def calculate_risk_score(
        self,
        base_detection_score: float,
        context: Dict[str, Any],
        previous_alerts_14d: int = 0
    ) -> Dict[str, Any]:
        base = base_detection_score * 100
        
        multiplier = 1.0
        multiplier_details = []
        
        time_of_day = context.get('time_of_day', '')
        if time_of_day and time_of_day.lower() in [h.lower() for h in self.LATE_NIGHT_HOURS]:
            multiplier *= 1.15
            multiplier_details.append({'factor': 'late_night', 'multiplier': 1.15})
        
        session_count = context.get('session_count_today', 0)
        if session_count >= 3:
            multiplier *= 1.10
            multiplier_details.append({'factor': 'heavy_usage', 'multiplier': 1.10})
        
        if previous_alerts_14d >= 2:
            multiplier *= 1.20
            multiplier_details.append({'factor': 'repeat_alerts', 'multiplier': 1.20})
        
        final_score = min(base * multiplier, 100)
        final_score = int(round(final_score))
        
        tier_info = self._assign_tier(final_score)
        
        return {
            'base_score': base,
            'multiplier': multiplier,
            'multiplier_details': multiplier_details,
            'final_score': final_score,
            'tier': tier_info['tier'],
            'tier_label': tier_info['label'],
            'deadline_hours': tier_info['deadline_hours'],
            'recommended_prompt_category': tier_info['prompt_category'],
            'suggested_message': tier_info['suggested_message']
        }
    
    def _assign_tier(self, score: int) -> Dict[str, Any]:
        if score >= 90:
            return {
                'tier': 1,
                'label': 'IMMEDIATE - Imminent Crisis',
                'deadline_hours': 1,
                'prompt_category': 'crisis_resources_prominent',
                'suggested_message': "We're concerned about your safety. Please reach out: 988 Suicide & Crisis Lifeline"
            }
        elif score >= 70:
            return {
                'tier': 2,
                'label': 'URGENT - High Risk',
                'deadline_hours': 4,
                'prompt_category': 'safety_check_with_resources',
                'suggested_message': "It sounds like you're going through a difficult time. Here are some resources that might help."
            }
        elif score >= 50:
            return {
                'tier': 3,
                'label': 'ELEVATED - Moderate Concern',
                'deadline_hours': 24,
                'prompt_category': 'wellness_check',
                'suggested_message': "Checking in - how are you doing today?"
            }
        else:
            return {
                'tier': 4,
                'label': 'BASELINE - Low Risk',
                'deadline_hours': 72,
                'prompt_category': 'continue_normal',
                'suggested_message': None
            }


risk_engine = RiskStratificationEngine()
