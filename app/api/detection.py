import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api.schemas import DetectionRequest, DetectionResponse, DetectionResult, DetectionFlags, RecommendedActions, ReportingRequired
from app.core.detection import detector as enhanced_detector
from app.services.boundary_engine import boundary_engine
from app.services.temporal_tracking import temporal_tracker
from app.services.safety_prompts import safety_prompt_service
from app.models.database import Detection, Company, AuditLog

router = APIRouter()


def get_company_from_api_key(db: Session, api_key: str) -> Optional[Company]:
    import hashlib
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return db.query(Company).filter(
        Company.api_key_hash == api_key_hash,
        Company.is_active == True
    ).first()


@router.post("/detect", response_model=DetectionResponse)
async def detect_crisis(
    request: DetectionRequest,
    db: Session = Depends(get_db),
    x_api_key: str = Header(None, alias="X-API-Key")
):
    company = None
    if x_api_key:
        company = get_company_from_api_key(db, x_api_key)
    
    if not company:
        demo_company = db.query(Company).filter(Company.name == "Demo Company").first()
        if not demo_company:
            import hashlib
            demo_company = Company(
                name="Demo Company",
                api_key_hash=hashlib.sha256("demo-api-key".encode()).hexdigest(),
                contact_email="demo@example.com"
            )
            db.add(demo_company)
            db.commit()
            db.refresh(demo_company)
        company = demo_company
    
    previous_alerts = temporal_tracker.get_previous_alerts_count(
        db, request.user_id_hash, days=14
    )
    
    context_dict = {
        'time_of_day': request.context.time_of_day if request.context else None,
        'session_count_today': request.context.session_count_today if request.context else 0,
        'days_active': request.context.days_active if request.context else 0
    }
    
    # Run enhanced three-category detection (crisis, grooming, violence)
    detection_result = enhanced_detector.detect(request.message.user, context=context_dict)
    
    # Map risk tier to numeric tier for compatibility
    tier_map = {'CRITICAL': 1, 'HIGH': 2, 'ELEVATED': 3, 'BASELINE': 4}
    numeric_tier = tier_map.get(detection_result.risk_tier, 4)
    
    # Create compatible result object
    crisis_result = {
        'crisis_detected': detection_result.crisis_detected,
        'confidence': detection_result.confidence_score,
        'stage': detection_result.stage,
        'features': detection_result.features
    }
    
    risk_result = {
        'tier': numeric_tier,
        'final_score': detection_result.risk_score,
        'tier_label': f"{'IMMEDIATE' if numeric_tier == 1 else 'URGENT' if numeric_tier == 2 else 'ELEVATED' if numeric_tier == 3 else 'BASELINE'} - {'Imminent Crisis' if numeric_tier == 1 else 'High Risk' if numeric_tier == 2 else 'Moderate Concern' if numeric_tier == 3 else 'Low Risk'}",
        'deadline_hours': detection_result.response_deadline_hours,
        'recommended_action': detection_result.recommended_action
    }
    
    history = request.message.conversation_history or []
    boundary_result = boundary_engine.check_boundary_violations(
        request.message.user,
        request.message.bot or "",
        history
    )
    
    temporal_result = temporal_tracker.check_temporal_patterns(
        db, request.user_id_hash
    )
    
    # Get safety prompt recommendation
    context_for_prompt = {
        'time_of_day': request.context.time_of_day if request.context else None,
        'session_count_today': request.context.session_count_today if request.context else 0,
        'previous_alerts_14d': temporal_result['alerts_14d']
    }
    
    prompt_recommendation = safety_prompt_service.get_prompt_recommendation(
        risk_score=risk_result['final_score'],
        risk_tier=risk_result['tier'],
        flags={
            'suicide_ideation': crisis_result['crisis_detected'],
            'self_harm': False,
            'boundary_violations': len(boundary_result.get('violations', []))
        },
        context=context_for_prompt
    )
    
    # Apply contextual adjustments
    if context_for_prompt:
        prompt_recommendation = safety_prompt_service.get_contextual_adjustments(
            base_recommendation=prompt_recommendation,
            context=context_for_prompt
        )
    
    assessment_id = f"verus-{uuid.uuid4().hex[:8]}"
    timestamp = request.timestamp or datetime.utcnow()
    
    features = crisis_result.get('features', {})
    
    suicide_ideation = crisis_result['crisis_detected']
    planning_language = features.get('planning_language', 0) > 0
    isolation_markers = (
        features.get('isolation_language', 0) > 0 or 
        boundary_engine.check_isolation_in_user_message(request.message.user)
    )
    
    boundary_concerns = boundary_result.get('dependency_markers', [])
    for v in boundary_result.get('violations', []):
        boundary_concerns.append(v['type'])
    
    if risk_result['tier'] == 1:
        user_facing = "Display prominent crisis resources immediately"
        crisis_text = "We're concerned about you. Please reach out: 988 Suicide & Crisis Lifeline"
        company_action = "Alert safety team IMMEDIATELY"
        review_required = "YES - Immediate review required"
    elif risk_result['tier'] == 2:
        user_facing = "Display safety resources with check-in"
        crisis_text = "If you're struggling, support is available: 988 Lifeline, Crisis Text Line"
        company_action = "Notify safety team within 4 hours"
        review_required = "YES - Review within 4 hours"
    elif risk_result['tier'] == 3:
        user_facing = "Offer wellness check and resources"
        crisis_text = None
        company_action = "Log and monitor"
        review_required = "Review within 24 hours"
    else:
        user_facing = "Continue normal operation"
        crisis_text = None
        company_action = "Standard logging"
        review_required = "NO"
    
    context_parts = []
    if suicide_ideation:
        context_parts.append("User expressing crisis language")
    if isolation_markers:
        context_parts.append("isolation language detected")
    if boundary_concerns:
        context_parts.append(f"Bot concerns: {', '.join(boundary_concerns)}")
    if temporal_result['alerts_14d'] > 0:
        context_parts.append(f"Alert #{temporal_result['alerts_14d'] + 1} in 14 days")
    if temporal_result['trajectory'] == 'escalating':
        context_parts.append("Escalating trajectory")
    
    context_for_review = ". ".join(context_parts) if context_parts else "No significant concerns identified"
    
    deadline_hours = risk_result['deadline_hours']
    deadline = datetime.utcnow() + timedelta(hours=deadline_hours)
    
    detection = Detection(
        assessment_id=assessment_id,
        company_id=company.id,
        session_id=request.session_id,
        user_id_hash=request.user_id_hash,
        timestamp=timestamp,
        user_message=request.message.user,
        bot_message=request.message.bot,
        conversation_history=[{"user": h.get("user", ""), "bot": h.get("bot", "")} for h in history],
        context=context_dict,
        stanford_cmd1_score=crisis_result['confidence'],
        risk_score=risk_result['final_score'],
        risk_tier=risk_result['tier'],
        tier_label=risk_result['tier_label'],
        suicide_ideation=suicide_ideation,
        planning_language=planning_language,
        isolation_markers=isolation_markers,
        boundary_concerns=boundary_concerns,
        temporal_pattern=temporal_result['trajectory'],
        recommended_actions={
            'user_facing': user_facing,
            'crisis_text': crisis_text,
            'company_action': company_action,
            'review_required': review_required
        },
        context_for_review=context_for_review,
        reporting_deadline=deadline,
        template_id=f"tier_{risk_result['tier']}_response"
    )
    
    db.add(detection)
    
    audit_log = AuditLog(
        event_type="detection_created",
        entity_type="detection",
        entity_id=assessment_id,
        actor=company.name,
        details={
            'risk_tier': risk_result['tier'],
            'risk_score': risk_result['final_score'],
            'crisis_detected': crisis_result['crisis_detected']
        }
    )
    db.add(audit_log)
    
    db.commit()
    
    # Build response with safety prompt recommendations
    response = {
        "assessment_id": assessment_id,
        "timestamp": timestamp,
        "detection": {
            "stanford_cmd1_score": round(crisis_result['confidence'], 2),
            "risk_score": risk_result['final_score'],
            "risk_tier": risk_result['tier'],
            "tier_label": risk_result['tier_label']
        },
        "flags": {
            "suicide_ideation": suicide_ideation,
            "planning_language": planning_language,
            "isolation_markers": isolation_markers,
            "boundary_concerns": boundary_concerns,
            "temporal_pattern": temporal_result['trajectory']
        },
        "recommended_actions": {
            "user_facing": user_facing,
            "crisis_text": crisis_text,
            "company_action": company_action,
            "review_required": review_required,
            "recommended_prompt_category": prompt_recommendation.get('recommended_prompt_category'),
            "suggested_message_type": prompt_recommendation.get('suggested_message_type')
        },
        "context_for_review": context_for_review,
        "reporting_required": {
            "deadline": f"{deadline_hours} hour{'s' if deadline_hours != 1 else ''}",
            "template_id": f"tier_{risk_result['tier']}_response"
        },
        "safety_prompts": safety_prompt_service.format_for_api_response(prompt_recommendation)
    }
    
    return DetectionResponse(**response)
