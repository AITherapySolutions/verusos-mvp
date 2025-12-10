import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class RiskTier(enum.Enum):
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3
    TIER_4 = 4


class ReviewStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"
    ESCALATED = "escalated"


class Company(Base):
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    api_key_hash = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    detections = relationship("Detection", back_populates="company")
    responses = relationship("CompanyResponse", back_populates="company")


class Detection(Base):
    __tablename__ = "detections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(String(50), unique=True, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    session_id = Column(String(255), nullable=False)
    user_id_hash = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user_message = Column(Text, nullable=False)
    bot_message = Column(Text)
    conversation_history = Column(JSON)
    context = Column(JSON)
    
    stanford_cmd1_score = Column(Float, nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_tier = Column(Integer, nullable=False)
    tier_label = Column(String(100), nullable=False)
    
    suicide_ideation = Column(Boolean, default=False)
    planning_language = Column(Boolean, default=False)
    isolation_markers = Column(Boolean, default=False)
    boundary_concerns = Column(JSON)
    temporal_pattern = Column(String(50))
    
    recommended_actions = Column(JSON)
    context_for_review = Column(Text)
    
    reporting_deadline = Column(DateTime)
    template_id = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company", back_populates="detections")
    response = relationship("CompanyResponse", back_populates="detection", uselist=False)
    review = relationship("ComplianceReview", back_populates="detection", uselist=False)


class CompanyResponse(Base):
    __tablename__ = "company_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    detection_id = Column(UUID(as_uuid=True), ForeignKey("detections.id"), nullable=False, unique=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    assessment_id = Column(String(50), nullable=False)
    
    timestamp_detection = Column(DateTime, nullable=False)
    timestamp_company_received = Column(DateTime)
    timestamp_company_responded = Column(DateTime)
    response_time_minutes = Column(Integer)
    
    detection_type = Column(String(100))
    risk_score = Column(Integer)
    risk_tier = Column(Integer)
    
    crisis_resources_displayed = Column(Boolean, default=False)
    resources_shown = Column(JSON)
    
    user_acknowledged_resources = Column(Boolean)
    user_clicked_resource = Column(Boolean)
    which_resource_clicked = Column(String(255))
    
    internal_actions = Column(JSON)
    
    escalation_required = Column(Boolean, default=False)
    escalation_reason = Column(Text)
    
    outcome_category = Column(String(100))
    outcome_details = Column(Text)
    follow_up_planned = Column(Boolean, default=False)
    
    protocol_followed = Column(String(100))
    protocol_document_version = Column(String(50))
    
    failure_to_respond = Column(Boolean, default=False)
    failure_reason = Column(Text)
    
    additional_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company", back_populates="responses")
    detection = relationship("Detection", back_populates="response")


class ComplianceReview(Base):
    __tablename__ = "compliance_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    detection_id = Column(UUID(as_uuid=True), ForeignKey("detections.id"), nullable=False, unique=True)
    reviewer_name = Column(String(255), default="Tammy")
    
    status = Column(String(50), default="pending")
    
    response_appropriate = Column(Boolean)
    resources_adequate = Column(Boolean)
    timing_acceptable = Column(Boolean)
    protocol_followed = Column(Boolean)
    
    reviewer_notes = Column(Text)
    revision_requested_reason = Column(Text)
    
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    detection = relationship("Detection", back_populates="review")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String(100), nullable=False)
    entity_type = Column(String(100))
    entity_id = Column(String(255))
    actor = Column(String(255))
    details = Column(JSON)
    ip_address = Column(String(50))
