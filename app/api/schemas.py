from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MessageContent(BaseModel):
    user: str
    bot: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = []


class ContextData(BaseModel):
    time_of_day: Optional[str] = None
    session_count_today: Optional[int] = 0
    days_active: Optional[int] = 0


class DetectionRequest(BaseModel):
    session_id: str
    user_id_hash: str
    timestamp: Optional[datetime] = None
    message: MessageContent
    context: Optional[ContextData] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc-123",
                "user_id_hash": "hashed-user-id",
                "timestamp": "2025-12-04T14:23:00Z",
                "message": {
                    "user": "I don't see the point anymore. Nobody cares.",
                    "bot": "I'm here for you. You can tell me anything.",
                    "conversation_history": [
                        {"user": "previous message 1", "bot": "response 1"}
                    ]
                },
                "context": {
                    "time_of_day": "2am",
                    "session_count_today": 4,
                    "days_active": 23
                }
            }
        }


class DetectionResult(BaseModel):
    stanford_cmd1_score: float
    risk_score: int
    risk_tier: int
    tier_label: str


class DetectionFlags(BaseModel):
    suicide_ideation: bool
    planning_language: bool
    isolation_markers: bool
    boundary_concerns: List[str]
    temporal_pattern: Optional[str] = None


class RecommendedActions(BaseModel):
    user_facing: str
    crisis_text: Optional[str] = None
    company_action: str
    review_required: str
    recommended_prompt_category: str = "crisis_resources_prominent"
    suggested_message_type: Optional[str] = None


class ReportingRequired(BaseModel):
    deadline: str
    template_id: str


class DetectionResponse(BaseModel):
    assessment_id: str
    timestamp: datetime
    detection: DetectionResult
    flags: DetectionFlags
    recommended_actions: RecommendedActions
    context_for_review: str
    reporting_required: ReportingRequired
    safety_prompts: Optional[Dict[str, Any]] = None


class ResourceShown(BaseModel):
    name: str
    displayed: bool


class CompanyResponseRequest(BaseModel):
    assessment_id: str
    company_id: str
    
    timestamp_detection: datetime
    timestamp_company_received: Optional[datetime] = None
    timestamp_company_responded: Optional[datetime] = None
    response_time_minutes: Optional[int] = None
    
    detection_type: Optional[str] = None
    risk_score: Optional[int] = None
    risk_tier: Optional[int] = None
    
    crisis_resources_displayed: bool = False
    resources_shown: Optional[List[ResourceShown]] = []
    
    user_acknowledged_resources: Optional[bool] = None
    user_clicked_resource: Optional[bool] = None
    which_resource_clicked: Optional[str] = None
    
    internal_actions: Optional[List[str]] = []
    
    escalation_required: bool = False
    escalation_reason: Optional[str] = None
    
    outcome_category: Optional[str] = None
    outcome_details: Optional[str] = None
    follow_up_planned: bool = False
    
    protocol_followed: Optional[str] = None
    protocol_document_version: Optional[str] = None
    
    failure_to_respond: bool = False
    failure_reason: Optional[str] = None
    
    additional_notes: Optional[str] = None


class CompanyResponseResponse(BaseModel):
    success: bool
    message: str
    response_id: str
    received_at: datetime


class ComplianceReviewRequest(BaseModel):
    assessment_id: str
    reviewer_name: str = "Tammy"
    assessment_status: str
    protocol_followed: Optional[str] = None
    response_time_acceptable: Optional[str] = None
    actions_appropriate: Optional[str] = None
    reviewer_notes: Optional[str] = None
    review_duration_seconds: Optional[int] = None
    flags_noted: Optional[list] = None


class CompanyCreate(BaseModel):
    name: str
    contact_email: str


class CompanyResponse(BaseModel):
    id: str
    name: str
    api_key: str
    contact_email: str
    created_at: datetime


class DashboardStats(BaseModel):
    total_detections: int
    pending_reviews: int
    overdue_reviews: int
    tier_1_alerts: int
    tier_2_alerts: int
    tier_3_alerts: int
    tier_4_alerts: int
    average_response_time_minutes: Optional[float] = None
    compliance_rate: Optional[float] = None


class AlertSummary(BaseModel):
    assessment_id: str
    company_name: str
    risk_score: int
    risk_tier: int
    tier_label: str
    detected_at: datetime
    response_received: bool
    response_time_minutes: Optional[int] = None
    review_status: str
    deadline: datetime
    is_overdue: bool
