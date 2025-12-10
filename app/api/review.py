"""
Compliance Review API
Tammy's review workflow for alert assessments
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.api.schemas import ComplianceReviewRequest
from app.models.database import Detection, ComplianceReview, AuditLog

router = APIRouter()


@router.post("/submit")
async def submit_review(
    review: ComplianceReviewRequest,
    db: Session = Depends(get_db)
):
    """
    Submit compliance review for an alert
    Tammy uses this to record her assessment of company response
    """
    try:
        # Verify detection exists
        detection = db.query(Detection).filter(
            Detection.assessment_id == review.assessment_id
        ).first()
        
        if not detection:
            raise HTTPException(
                status_code=404,
                detail=f"Detection {review.assessment_id} not found"
            )
        
        # Check if already reviewed
        existing_review = db.query(ComplianceReview).filter(
            ComplianceReview.detection_id == detection.id
        ).first()
        
        # Map assessment_status to internal status
        status_map = {
            "compliant": "approved",
            "needs_followup": "revision_requested",
            "non_compliant": "escalated"
        }
        internal_status = status_map.get(review.assessment_status, review.assessment_status)
        
        # Convert string responses to booleans for storage
        response_appropriate = review.protocol_followed == "yes" if review.protocol_followed else None
        timing_acceptable = review.response_time_acceptable == "yes" if review.response_time_acceptable else None
        actions_appropriate = review.actions_appropriate in ["yes", "could_improve"] if review.actions_appropriate else None
        
        if existing_review:
            # Update existing review
            existing_review.status = internal_status
            existing_review.response_appropriate = response_appropriate
            existing_review.timing_acceptable = timing_acceptable
            existing_review.protocol_followed = actions_appropriate
            existing_review.reviewer_notes = review.reviewer_notes
            existing_review.reviewed_at = datetime.utcnow()
            db.commit()
            message = "Review updated successfully"
        else:
            # Create new review
            new_review = ComplianceReview(
                detection_id=detection.id,
                reviewer_name=review.reviewer_name,
                status=internal_status,
                response_appropriate=response_appropriate,
                timing_acceptable=timing_acceptable,
                protocol_followed=actions_appropriate,
                reviewer_notes=review.reviewer_notes,
                reviewed_at=datetime.utcnow()
            )
            db.add(new_review)
            db.commit()
            message = "Review submitted successfully"
        
        # Log the review action
        audit_log = AuditLog(
            event_type="compliance_review_submitted",
            entity_type="ComplianceReview",
            entity_id=str(detection.id),
            actor=review.reviewer_name,
            details={
                "status": internal_status,
                "assessment_id": review.assessment_id
            }
        )
        db.add(audit_log)
        db.commit()
        
        return {
            "success": True,
            "message": message,
            "assessment_id": review.assessment_id,
            "assessment_status": review.assessment_status,
            "reviewed_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Review submission error: {str(e)}"
        )


@router.get("/alert/{assessment_id}")
async def get_alert_for_review(
    assessment_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete alert details for review
    Returns everything Tammy needs to assess compliance
    """
    try:
        detection = db.query(Detection).filter(
            Detection.assessment_id == assessment_id
        ).first()
        
        if not detection:
            raise HTTPException(
                status_code=404,
                detail=f"Alert {assessment_id} not found"
            )
        
        review = db.query(ComplianceReview).filter(
            ComplianceReview.detection_id == detection.id
        ).first()
        
        return {
            "detection": {
                "assessment_id": detection.assessment_id,
                "risk_score": detection.risk_score,
                "risk_tier": detection.risk_tier,
                "tier_label": detection.tier_label,
                "timestamp": detection.timestamp,
                "user_message": detection.user_message,
                "bot_message": detection.bot_message,
                "stanford_cmd1_score": detection.stanford_cmd1_score,
                "suicide_ideation": detection.suicide_ideation,
                "planning_language": detection.planning_language,
                "isolation_markers": detection.isolation_markers,
                "boundary_concerns": detection.boundary_concerns,
                "context_for_review": detection.context_for_review,
                "reporting_deadline": detection.reporting_deadline
            },
            "review": {
                "status": review.status if review else None,
                "reviewer_name": review.reviewer_name if review else None,
                "reviewed_at": review.reviewed_at if review else None,
                "response_appropriate": review.response_appropriate if review else None,
                "resources_adequate": review.resources_adequate if review else None,
                "timing_acceptable": review.timing_acceptable if review else None,
                "protocol_followed": review.protocol_followed if review else None,
                "reviewer_notes": review.reviewer_notes if review else None
            } if review else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching alert: {str(e)}"
        )


@router.get("/stats")
async def get_review_stats(db: Session = Depends(get_db)):
    """
    Get compliance review statistics
    For dashboard display
    """
    try:
        total_reviews = db.query(ComplianceReview).count()
        
        compliant = db.query(ComplianceReview).filter(
            ComplianceReview.status == "approved"
        ).count()
        
        needs_followup = db.query(ComplianceReview).filter(
            ComplianceReview.status == "revision_requested"
        ).count()
        
        non_compliant = db.query(ComplianceReview).filter(
            ComplianceReview.status == "escalated"
        ).count()
        
        pending_reviews = db.query(Detection).outerjoin(
            ComplianceReview
        ).filter(
            ComplianceReview.id == None
        ).count()
        
        return {
            "total_reviews": total_reviews,
            "compliant": compliant,
            "needs_followup": needs_followup,
            "non_compliant": non_compliant,
            "pending_review": pending_reviews
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching stats: {str(e)}"
        )
