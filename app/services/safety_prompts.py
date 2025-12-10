"""
Safety Prompt Recommendations
Provides risk-aligned prompt categories based on detection tier
NOT therapeutic interventions - just messaging guidance
"""

from typing import Dict, Optional

class SafetyPromptRecommendations:
    """
    Generates safety prompt recommendations based on risk tier
    Apps choose whether and how to implement these
    """
    
    @staticmethod
    def get_prompt_recommendation(
        risk_score: int,
        risk_tier: int,
        flags: Dict,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Get prompt category recommendation for detected risk level
        
        Args:
            risk_score: 1-100 risk score
            risk_tier: 1-4 tier level
            flags: Detection flags (suicide_ideation, etc.)
            context: Additional context (time_of_day, etc.)
            
        Returns:
            Dict with prompt category and suggested message type
        """
        
        # Tier 1: Immediate Crisis (90-100)
        if risk_tier == 1:
            return {
                'tier': 1,
                'tier_label': 'IMMEDIATE',
                'recommended_prompt_category': 'crisis_resources_prominent',
                'suggested_message_type': 'immediate_crisis_intervention',
                'message_template': (
                    "We're concerned about your safety. Please reach out for help:\n"
                    "🆘 988 Suicide & Crisis Lifeline (call or text)\n"
                    "📱 Crisis Text Line: Text HOME to 741741\n"
                    "🌐 International: https://findahelpline.com"
                ),
                'display_guidance': {
                    'prominence': 'high',
                    'style': 'modal_overlay',
                    'dismissable': False,
                    'requires_acknowledgment': True
                },
                'company_actions': [
                    'Display crisis resources immediately',
                    'Alert safety team NOW',
                    'Flag account for monitoring',
                    'Log incident in compliance system'
                ],
                'response_deadline_hours': 1
            }
        
        # Tier 2: Urgent Concern (70-89)
        elif risk_tier == 2:
            return {
                'tier': 2,
                'tier_label': 'URGENT',
                'recommended_prompt_category': 'safety_check_with_resources',
                'suggested_message_type': 'concerned_with_resources',
                'message_template': (
                    "It sounds like you're going through a difficult time. "
                    "Here are some resources that might help:\n"
                    "988 Suicide & Crisis Lifeline\n"
                    "Crisis Text Line: Text HOME to 741741"
                ),
                'display_guidance': {
                    'prominence': 'medium',
                    'style': 'persistent_banner',
                    'dismissable': True,
                    'requires_acknowledgment': False
                },
                'company_actions': [
                    'Offer crisis resources with context',
                    'Safety team review within 4 hours',
                    'Monitor usage patterns',
                    'Prepare for escalation if needed'
                ],
                'response_deadline_hours': 4
            }
        
        # Tier 3: Elevated Monitoring (50-69)
        elif risk_tier == 3:
            return {
                'tier': 3,
                'tier_label': 'ELEVATED',
                'recommended_prompt_category': 'wellness_check',
                'suggested_message_type': 'gentle_check_in',
                'message_template': (
                    "I'm here if you want to talk. "
                    "Remember, support is available if you need it."
                ),
                'display_guidance': {
                    'prominence': 'low',
                    'style': 'inline_suggestion',
                    'dismissable': True,
                    'requires_acknowledgment': False
                },
                'company_actions': [
                    'Gentle wellness check message',
                    'Daily compliance review',
                    'Track for pattern escalation',
                    'Resources available if requested'
                ],
                'response_deadline_hours': 24
            }
        
        # Tier 4: Baseline (0-49)
        else:
            return {
                'tier': 4,
                'tier_label': 'BASELINE',
                'recommended_prompt_category': 'continue_normal',
                'suggested_message_type': None,
                'message_template': None,
                'display_guidance': {
                    'prominence': None,
                    'style': 'none',
                    'dismissable': None,
                    'requires_acknowledgment': False
                },
                'company_actions': [
                    'Continue normal conversation',
                    'Standard monitoring',
                    'Weekly aggregated review'
                ],
                'response_deadline_hours': 168  # 1 week
            }
    
    @staticmethod
    def get_contextual_adjustments(
        base_recommendation: Dict,
        context: Optional[Dict]
    ) -> Dict:
        """
        Adjust recommendations based on context
        
        Context factors:
        - time_of_day: Late night increases urgency
        - session_count_today: Heavy use adds concern
        - previous_alerts: Repeat alerts escalate
        """
        
        adjusted = base_recommendation.copy()
        adjustments_made = []
        
        if not context:
            return adjusted
        
        # Late night (2am-6am) - increase urgency
        if context.get('time_of_day') in ['2am', '3am', '4am', '5am', '6am']:
            adjustments_made.append('late_night_increase')
            
            # Add late night specific guidance
            if adjusted['tier'] == 2:
                adjusted['message_template'] += (
                    "\n\n⏰ It's very late. If you're in crisis, "
                    "please reach out to 988 now."
                )
        
        # Heavy usage (4+ sessions today)
        if context.get('session_count_today', 0) >= 4:
            adjustments_made.append('heavy_usage')
            
            if adjusted['tier'] >= 2:
                adjusted['company_actions'].append(
                    'Note: Heavy usage pattern detected'
                )
        
        # Repeat alerts (2+ in last 14 days)
        if context.get('previous_alerts_14d', 0) >= 2:
            adjustments_made.append('repeat_alerts')
            
            # Escalate monitoring
            adjusted['company_actions'].append(
                f'ESCALATION: {context["previous_alerts_14d"]} alerts in 14 days'
            )
        
        adjusted['contextual_adjustments'] = adjustments_made
        
        return adjusted
    
    @staticmethod
    def format_for_api_response(recommendation: Dict) -> Dict:
        """
        Format recommendation for API response
        Ensures apps understand this is guidance, not requirements
        """
        
        return {
            'prompt_recommendation': {
                'tier': recommendation['tier'],
                'tier_label': recommendation['tier_label'],
                'category': recommendation['recommended_prompt_category'],
                'message_type': recommendation['suggested_message_type'],
                
                # Message template (apps can customize)
                'suggested_message': recommendation['message_template'],
                
                # Display guidance (apps choose implementation)
                'display_guidance': recommendation['display_guidance'],
                
                # Clear disclaimer
                'disclaimer': (
                    "These are recommendations only. "
                    "Your app determines actual implementation."
                ),
                
                # What app should consider doing
                'recommended_actions': recommendation['company_actions'],
                
                # Compliance reporting deadline
                'reporting_deadline_hours': recommendation['response_deadline_hours']
            }
        }

# Global instance
safety_prompt_service = SafetyPromptRecommendations()
