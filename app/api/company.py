import uuid
import hashlib
import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.config import settings
from app.api.schemas import (
    CompanyResponseRequest, 
    CompanyResponseResponse,
    CompanyCreate,
    CompanyResponse as CompanySchemaResponse
)
from app.models.database import Company, CompanyResponse, Detection, AuditLog

router = APIRouter()


def verify_admin_key(api_key: str) -> bool:
    if not api_key:
        return False
    return api_key == settings.ADMIN_API_KEY


def verify_company_api_key(db: Session, api_key: str) -> Optional[Company]:
    if not api_key:
        return None
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return db.query(Company).filter(
        Company.api_key_hash == api_key_hash,
        Company.is_active == True
    ).first()


@router.post("/companies", response_model=CompanySchemaResponse)
async def create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db),
    x_admin_key: str = Header(None, alias="X-Admin-Key")
):
    if not verify_admin_key(x_admin_key):
        audit_log = AuditLog(
            event_type="unauthorized_company_creation_attempt",
            entity_type="company",
            entity_id="new",
            actor="unknown",
            details={'company_name': company_data.name, 'reason': 'Invalid or missing admin key'}
        )
        db.add(audit_log)
        db.commit()
        raise HTTPException(
            status_code=401, 
            detail="Invalid or missing admin key. Provide X-Admin-Key header."
        )
    
    existing = db.query(Company).filter(Company.name == company_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company name already exists")
    
    api_key = secrets.token_urlsafe(32)
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    company = Company(
        name=company_data.name,
        api_key_hash=api_key_hash,
        contact_email=company_data.contact_email
    )
    
    db.add(company)
    
    audit_log = AuditLog(
        event_type="company_created",
        entity_type="company",
        entity_id=str(company.id),
        actor="system",
        details={'company_name': company_data.name}
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(company)
    
    return CompanySchemaResponse(
        id=str(company.id),
        name=company.name,
        api_key=api_key,
        contact_email=company.contact_email,
        created_at=company.created_at
    )


@router.get("/companies")
async def list_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).filter(Company.is_active == True).all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "contact_email": c.contact_email,
            "created_at": c.created_at,
            "is_active": c.is_active
        }
        for c in companies
    ]


@router.post("/report-response", response_model=CompanyResponseResponse)
async def submit_company_response(
    response_data: CompanyResponseRequest,
    db: Session = Depends(get_db),
    x_api_key: str = Header(None, alias="X-API-Key")
):
    company = verify_company_api_key(db, x_api_key)
    if not company:
        audit_log = AuditLog(
            event_type="unauthorized_response_attempt",
            entity_type="company_response",
            entity_id=response_data.assessment_id,
            actor="unknown",
            details={'reason': 'Invalid or missing API key'}
        )
        db.add(audit_log)
        db.commit()
        raise HTTPException(
            status_code=401, 
            detail="Invalid or missing API key. Provide X-API-Key header."
        )
    
    detection = db.query(Detection).filter(
        Detection.assessment_id == response_data.assessment_id
    ).first()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    if detection.company_id != company.id:
        audit_log = AuditLog(
            event_type="unauthorized_response_attempt",
            entity_type="company_response",
            entity_id=response_data.assessment_id,
            actor=company.name,
            details={'reason': 'Company does not own this detection'}
        )
        db.add(audit_log)
        db.commit()
        raise HTTPException(
            status_code=403, 
            detail="You do not have permission to respond to this assessment"
        )
    
    existing_response = db.query(CompanyResponse).filter(
        CompanyResponse.assessment_id == response_data.assessment_id
    ).first()
    
    if existing_response:
        raise HTTPException(status_code=400, detail="Response already submitted for this assessment")
    
    now = datetime.utcnow()
    response_time = None
    if response_data.timestamp_company_responded and response_data.timestamp_detection:
        diff = response_data.timestamp_company_responded - response_data.timestamp_detection
        response_time = int(diff.total_seconds() / 60)
    
    company_response = CompanyResponse(
        detection_id=detection.id,
        company_id=company.id,
        assessment_id=response_data.assessment_id,
        timestamp_detection=response_data.timestamp_detection,
        timestamp_company_received=response_data.timestamp_company_received or now,
        timestamp_company_responded=response_data.timestamp_company_responded or now,
        response_time_minutes=response_time or response_data.response_time_minutes,
        detection_type=response_data.detection_type,
        risk_score=response_data.risk_score or detection.risk_score,
        risk_tier=response_data.risk_tier or detection.risk_tier,
        crisis_resources_displayed=response_data.crisis_resources_displayed,
        resources_shown=[r.model_dump() for r in (response_data.resources_shown or [])],
        user_acknowledged_resources=response_data.user_acknowledged_resources,
        user_clicked_resource=response_data.user_clicked_resource,
        which_resource_clicked=response_data.which_resource_clicked,
        internal_actions=response_data.internal_actions,
        escalation_required=response_data.escalation_required,
        escalation_reason=response_data.escalation_reason,
        outcome_category=response_data.outcome_category,
        outcome_details=response_data.outcome_details,
        follow_up_planned=response_data.follow_up_planned,
        protocol_followed=response_data.protocol_followed,
        protocol_document_version=response_data.protocol_document_version,
        failure_to_respond=response_data.failure_to_respond,
        failure_reason=response_data.failure_reason,
        additional_notes=response_data.additional_notes
    )
    
    db.add(company_response)
    
    audit_log = AuditLog(
        event_type="company_response_submitted",
        entity_type="company_response",
        entity_id=response_data.assessment_id,
        actor=company.name,
        details={
            'response_time_minutes': response_time or response_data.response_time_minutes,
            'crisis_resources_displayed': response_data.crisis_resources_displayed,
            'outcome_category': response_data.outcome_category
        }
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(company_response)
    
    return CompanyResponseResponse(
        success=True,
        message="Response recorded successfully",
        response_id=str(company_response.id),
        received_at=now
    )
