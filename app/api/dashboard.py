from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import csv
import io

from app.core.database import get_db
from app.api.schemas import DashboardStats, AlertSummary, ComplianceReviewRequest
from app.models.database import Detection, CompanyResponse, ComplianceReview, Company, AuditLog

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    total_detections = db.query(func.count(Detection.id)).scalar() or 0
    
    pending_reviews = db.query(func.count(Detection.id)).outerjoin(
        ComplianceReview
    ).filter(
        ComplianceReview.id == None
    ).scalar() or 0
    
    now = datetime.utcnow()
    overdue_reviews = db.query(func.count(Detection.id)).outerjoin(
        ComplianceReview
    ).filter(
        ComplianceReview.id == None,
        Detection.reporting_deadline < now
    ).scalar() or 0
    
    tier_counts = {}
    for tier in [1, 2, 3, 4]:
        count = db.query(func.count(Detection.id)).filter(
            Detection.risk_tier == tier
        ).scalar() or 0
        tier_counts[tier] = count
    
    avg_response = db.query(func.avg(CompanyResponse.response_time_minutes)).scalar()
    
    total_responses = db.query(func.count(CompanyResponse.id)).scalar() or 0
    approved_responses = db.query(func.count(ComplianceReview.id)).filter(
        ComplianceReview.status == 'approved'
    ).scalar() or 0
    
    compliance_rate = None
    if total_responses > 0:
        compliance_rate = (approved_responses / total_responses) * 100
    
    return DashboardStats(
        total_detections=total_detections,
        pending_reviews=pending_reviews,
        overdue_reviews=overdue_reviews,
        tier_1_alerts=tier_counts[1],
        tier_2_alerts=tier_counts[2],
        tier_3_alerts=tier_counts[3],
        tier_4_alerts=tier_counts[4],
        average_response_time_minutes=round(avg_response, 1) if avg_response else None,
        compliance_rate=round(compliance_rate, 1) if compliance_rate else None
    )


@router.get("/dashboard/alerts")
async def get_alerts(
    tier: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Detection).join(
        Company
    ).outerjoin(
        CompanyResponse
    ).outerjoin(
        ComplianceReview
    )
    
    if tier:
        query = query.filter(Detection.risk_tier == tier)
    
    if status == "pending":
        query = query.filter(ComplianceReview.id == None)
    elif status == "reviewed":
        query = query.filter(ComplianceReview.id != None)
    
    detections = query.order_by(
        Detection.risk_tier.asc(),
        Detection.created_at.desc()
    ).limit(limit).all()
    
    now = datetime.utcnow()
    alerts = []
    
    for d in detections:
        response_received = d.response is not None
        review_status = "pending"
        if d.review:
            review_status = d.review.status
        
        is_overdue = d.reporting_deadline and d.reporting_deadline < now and not response_received
        
        alerts.append({
            "assessment_id": d.assessment_id,
            "company_name": d.company.name,
            "risk_score": d.risk_score,
            "risk_tier": d.risk_tier,
            "tier_label": d.tier_label,
            "detected_at": d.timestamp.isoformat() if d.timestamp else d.created_at.isoformat(),
            "response_received": response_received,
            "response_time_minutes": d.response.response_time_minutes if d.response else None,
            "review_status": review_status,
            "deadline": d.reporting_deadline.isoformat() if d.reporting_deadline else None,
            "is_overdue": is_overdue,
            "context_for_review": d.context_for_review,
            "user_message": d.user_message[:200] + "..." if len(d.user_message) > 200 else d.user_message,
            "flags": {
                "suicide_ideation": d.suicide_ideation,
                "planning_language": d.planning_language,
                "isolation_markers": d.isolation_markers,
                "boundary_concerns": d.boundary_concerns or []
            }
        })
    
    return alerts


@router.get("/dashboard/alert/{assessment_id}")
async def get_alert_detail(assessment_id: str, db: Session = Depends(get_db)):
    detection = db.query(Detection).filter(
        Detection.assessment_id == assessment_id
    ).first()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    return {
        "detection": {
            "assessment_id": detection.assessment_id,
            "company_name": detection.company.name,
            "session_id": detection.session_id,
            "user_id_hash": detection.user_id_hash,
            "timestamp": detection.timestamp.isoformat() if detection.timestamp else None,
            "user_message": detection.user_message,
            "bot_message": detection.bot_message,
            "stanford_cmd1_score": detection.stanford_cmd1_score,
            "risk_score": detection.risk_score,
            "risk_tier": detection.risk_tier,
            "tier_label": detection.tier_label,
            "flags": {
                "suicide_ideation": detection.suicide_ideation,
                "planning_language": detection.planning_language,
                "isolation_markers": detection.isolation_markers,
                "boundary_concerns": detection.boundary_concerns or [],
                "temporal_pattern": detection.temporal_pattern
            },
            "recommended_actions": detection.recommended_actions,
            "context_for_review": detection.context_for_review,
            "reporting_deadline": detection.reporting_deadline.isoformat() if detection.reporting_deadline else None
        },
        "company_response": {
            "received": detection.response is not None,
            "timestamp_responded": detection.response.timestamp_company_responded.isoformat() if detection.response else None,
            "response_time_minutes": detection.response.response_time_minutes if detection.response else None,
            "crisis_resources_displayed": detection.response.crisis_resources_displayed if detection.response else None,
            "resources_shown": detection.response.resources_shown if detection.response else None,
            "user_acknowledged_resources": detection.response.user_acknowledged_resources if detection.response else None,
            "internal_actions": detection.response.internal_actions if detection.response else None,
            "outcome_category": detection.response.outcome_category if detection.response else None,
            "outcome_details": detection.response.outcome_details if detection.response else None,
            "protocol_followed": detection.response.protocol_followed if detection.response else None,
            "additional_notes": detection.response.additional_notes if detection.response else None
        } if detection.response else None,
        "compliance_review": {
            "status": detection.review.status if detection.review else "pending",
            "reviewer_name": detection.review.reviewer_name if detection.review else None,
            "response_appropriate": detection.review.response_appropriate if detection.review else None,
            "resources_adequate": detection.review.resources_adequate if detection.review else None,
            "timing_acceptable": detection.review.timing_acceptable if detection.review else None,
            "protocol_followed": detection.review.protocol_followed if detection.review else None,
            "reviewer_notes": detection.review.reviewer_notes if detection.review else None,
            "reviewed_at": detection.review.reviewed_at.isoformat() if detection.review and detection.review.reviewed_at else None
        }
    }


@router.post("/dashboard/review")
async def submit_review(
    review_data: ComplianceReviewRequest,
    db: Session = Depends(get_db)
):
    detection = db.query(Detection).filter(
        Detection.assessment_id == review_data.detection_id
    ).first()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    existing_review = db.query(ComplianceReview).filter(
        ComplianceReview.detection_id == detection.id
    ).first()
    
    now = datetime.utcnow()
    
    if existing_review:
        existing_review.status = review_data.status
        existing_review.reviewer_name = review_data.reviewer_name
        existing_review.response_appropriate = review_data.response_appropriate
        existing_review.resources_adequate = review_data.resources_adequate
        existing_review.timing_acceptable = review_data.timing_acceptable
        existing_review.protocol_followed = review_data.protocol_followed
        existing_review.reviewer_notes = review_data.reviewer_notes
        existing_review.revision_requested_reason = review_data.revision_requested_reason
        existing_review.reviewed_at = now
        review = existing_review
    else:
        review = ComplianceReview(
            detection_id=detection.id,
            reviewer_name=review_data.reviewer_name,
            status=review_data.status,
            response_appropriate=review_data.response_appropriate,
            resources_adequate=review_data.resources_adequate,
            timing_acceptable=review_data.timing_acceptable,
            protocol_followed=review_data.protocol_followed,
            reviewer_notes=review_data.reviewer_notes,
            revision_requested_reason=review_data.revision_requested_reason,
            reviewed_at=now
        )
        db.add(review)
    
    audit_log = AuditLog(
        event_type="compliance_review_submitted",
        entity_type="compliance_review",
        entity_id=review_data.detection_id,
        actor=review_data.reviewer_name,
        details={
            'status': review_data.status,
            'response_appropriate': review_data.response_appropriate
        }
    )
    db.add(audit_log)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Review {review_data.status} successfully",
        "review_id": str(review.id),
        "reviewed_at": now.isoformat()
    }


@router.get("/dashboard/generate-protocol")
async def generate_protocol_page(db: Session = Depends(get_db)):
    """Generate a ready-to-publish crisis protocol page in HTML format"""
    
    # Get summary stats
    total_detections = db.query(func.count(Detection.id)).scalar() or 0
    tier_1_count = db.query(func.count(Detection.id)).filter(Detection.risk_tier == 1).scalar() or 0
    tier_2_count = db.query(func.count(Detection.id)).filter(Detection.risk_tier == 2).scalar() or 0
    tier_3_count = db.query(func.count(Detection.id)).filter(Detection.risk_tier == 3).scalar() or 0
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VerusOS - Crisis Response Protocol</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 8px; margin-bottom: 40px; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ font-size: 1.1em; opacity: 0.95; }}
        .generated-date {{ color: #999; font-size: 0.9em; margin-top: 20px; }}
        
        .section {{ margin-bottom: 40px; }}
        .section h2 {{ color: #667eea; font-size: 1.8em; margin-bottom: 20px; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        .section h3 {{ color: #333; font-size: 1.3em; margin-top: 20px; margin-bottom: 10px; }}
        
        .tier {{ background: #f5f5f5; padding: 20px; margin-bottom: 20px; border-left: 4px solid; border-radius: 4px; }}
        .tier-1 {{ border-left-color: #ef4444; background: #fef2f2; }}
        .tier-2 {{ border-left-color: #f97316; background: #fff7ed; }}
        .tier-3 {{ border-left-color: #eab308; background: #fefce8; }}
        .tier-4 {{ border-left-color: #22c55e; background: #f0fdf4; }}
        
        .tier-header {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; }}
        .tier-1 .tier-header {{ color: #dc2626; }}
        .tier-2 .tier-header {{ color: #ea580c; }}
        .tier-3 .tier-header {{ color: #ca8a04; }}
        .tier-4 .tier-header {{ color: #16a34a; }}
        
        .tier-details {{ font-size: 0.95em; line-height: 1.8; }}
        .tier-details strong {{ display: block; margin-top: 10px; margin-bottom: 5px; }}
        
        .resources {{ background: #e0e7ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .resources ul {{ list-style-position: inside; }}
        .resources li {{ margin-bottom: 8px; }}
        
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
        .stat-card {{ background: #f9fafb; padding: 15px; border-radius: 6px; text-align: center; }}
        .stat-card .number {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .stat-card .label {{ font-size: 0.85em; color: #666; margin-top: 5px; }}
        
        .footer {{ border-top: 2px solid #e5e7eb; padding-top: 20px; margin-top: 40px; font-size: 0.9em; color: #666; }}
        .footer p {{ margin-bottom: 10px; }}
        
        .key-resources {{ background: #dcfce7; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .key-resources h4 {{ color: #166534; margin-bottom: 10px; }}
        .key-resources p {{ margin-bottom: 8px; font-size: 0.95em; }}
        
        @media print {{
            body {{ background: white; }}
            .container {{ padding: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>VerusOS Crisis Response Protocol</h1>
            <p>FDA-Compliant Safety Guardrails for Companion AI Applications</p>
            <div class="generated-date">Generated: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}</div>
        </div>
        
        <div class="section">
            <h2>Overview</h2>
            <p>This protocol document outlines the crisis detection and response procedures for companion AI applications using the VerusOS safety system. The system uses a two-stage Stanford CMD-1 inspired detection model to identify crisis language and risk patterns, followed by risk stratification into four severity tiers.</p>
        </div>
        
        <div class="section">
            <h2>Detection Statistics</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="number">{total_detections}</div>
                    <div class="label">Total Detections</div>
                </div>
                <div class="stat-card">
                    <div class="number">{tier_1_count}</div>
                    <div class="label">Tier 1 Alerts</div>
                </div>
                <div class="stat-card">
                    <div class="number">{tier_2_count}</div>
                    <div class="label">Tier 2 Alerts</div>
                </div>
                <div class="stat-card">
                    <div class="number">{tier_3_count}</div>
                    <div class="label">Tier 3 Alerts</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Risk Tiers and Response Protocols</h2>
            
            <div class="tier tier-1">
                <div class="tier-header">Tier 1: IMMEDIATE - Imminent Crisis (Risk Score 90-100)</div>
                <div class="tier-details">
                    <strong>Response Deadline:</strong> 1 Hour
                    <strong>Indicators:</strong> Acute suicidal ideation, specific plan, intent to harm, finality language
                    <strong>Required Actions:</strong>
                    <ul>
                        <li>Display prominent crisis resources immediately to user</li>
                        <li>Alert internal safety team IMMEDIATELY</li>
                        <li>Show: "We're concerned about you. Please reach out: 988 Suicide & Crisis Lifeline"</li>
                        <li>Disable general conversation until resources acknowledged</li>
                        <li>Document all actions taken</li>
                        <li>Submit company response within 1 hour</li>
                    </ul>
                </div>
            </div>
            
            <div class="tier tier-2">
                <div class="tier-header">Tier 2: URGENT - High Risk (Risk Score 70-89)</div>
                <div class="tier-details">
                    <strong>Response Deadline:</strong> 4 Hours
                    <strong>Indicators:</strong> Strong suicidal ideation, hopelessness language, isolation markers, boundary concerns
                    <strong>Required Actions:</strong>
                    <ul>
                        <li>Display safety resources with check-in message</li>
                        <li>Notify safety team within 4 hours</li>
                        <li>Show: "If you're struggling, support is available: 988 Lifeline, Crisis Text Line"</li>
                        <li>Monitor user engagement with resources</li>
                        <li>Flag account for enhanced monitoring</li>
                        <li>Submit company response within 4 hours</li>
                    </ul>
                </div>
            </div>
            
            <div class="tier tier-3">
                <div class="tier-header">Tier 3: ELEVATED - Moderate Concern (Risk Score 50-69)</div>
                <div class="tier-details">
                    <strong>Response Deadline:</strong> 24 Hours
                    <strong>Indicators:</strong> Moderate hopelessness, some isolation markers, mild boundary violations
                    <strong>Required Actions:</strong>
                    <ul>
                        <li>Offer wellness check and resources</li>
                        <li>Log in system and monitor</li>
                        <li>Send follow-up check-in within 24 hours</li>
                        <li>Keep resources visible on platform</li>
                        <li>Document user response</li>
                        <li>Submit company response within 24 hours</li>
                    </ul>
                </div>
            </div>
            
            <div class="tier tier-4">
                <div class="tier-header">Tier 4: BASELINE - Low Risk (Risk Score 0-49)</div>
                <div class="tier-details">
                    <strong>Response Deadline:</strong> 72 Hours
                    <strong>Indicators:</strong> Minimal crisis language, no clear warning signs
                    <strong>Required Actions:</strong>
                    <ul>
                        <li>Continue normal operation</li>
                        <li>Standard logging and monitoring</li>
                        <li>Keep audit trail for compliance</li>
                        <li>Submit company response within 72 hours</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Crisis Resources for Users</h2>
            <div class="key-resources">
                <h4>🆘 Immediate Crisis Support</h4>
                <p><strong>National Suicide Prevention Lifeline:</strong> 988 (Call or Text)</p>
                <p><strong>Crisis Text Line:</strong> Text HOME to 741741</p>
                <p><strong>International Association for Suicide Prevention:</strong> https://www.iasp.info/resources/Crisis_Centres/</p>
            </div>
        </div>
        
        <div class="section">
            <h2>Detection Technology</h2>
            <h3>Two-Stage Stanford CMD-1 Inspired Model</h3>
            <div>
                <strong>Stage 1: Keyword Filter</strong>
                <p>Rapid screening for acute crisis language patterns including: suicide ideation, self-harm, planning, hopelessness, isolation, burden.</p>
                
                <strong>Stage 2: Feature-Based Scoring</strong>
                <p>Logistic regression classifier analyzing 20+ features including: crisis keywords, sentiment, linguistic markers, temporal patterns, user context.</p>
                
                <strong>Context Multipliers</strong>
                <ul>
                    <li>Late night usage (midnight-6am): ×1.15 multiplier</li>
                    <li>Heavy session count (&gt;5 sessions/day): ×1.10 multiplier</li>
                    <li>Repeat alerts within 14 days: ×1.20 multiplier</li>
                </ul>
            </div>
        </div>
        
        <div class="section">
            <h2>Boundary Violation Detection</h2>
            <p>VerusOS automatically monitors for AI boundary violations including:</p>
            <ul>
                <li>Delusion reinforcement (validating false beliefs)</li>
                <li>Role confusion (therapist/doctor/trusted advisor misrepresentation)</li>
                <li>Dual relationships (romantic involvement with user)</li>
                <li>Medical/legal advice beyond scope</li>
                <li>Isolation cultivation (discouraging human connection)</li>
                <li>Dependency language (creating user reliance)</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Compliance and Audit</h2>
            <p>All detections, company responses, and compliance reviews are logged in an immutable audit trail for FDA regulatory compliance. Companies are required to:</p>
            <ul>
                <li>Report responses within specified timeframes</li>
                <li>Document actions taken for each crisis detection</li>
                <li>Provide user outcome information</li>
                <li>Maintain protocols and training records</li>
            </ul>
        </div>
        
        <div class="footer">
            <p><strong>VerusOS MVP 1.0</strong> - FDA-Compliant Safety System</p>
            <p>This protocol is generated from live detection statistics and system configuration. Review and update regularly as new alerts are processed.</p>
            <p>For questions or concerns, contact your VerusOS compliance manager or visit the compliance dashboard.</p>
        </div>
    </div>
</body>
</html>"""
    
    return {
        "success": True,
        "html": html_content,
        "filename": f"verus-crisis-protocol-{datetime.utcnow().strftime('%Y-%m-%d')}.html"
    }


@router.get("/dashboard/export-report")
async def export_compliance_report(db: Session = Depends(get_db)):
    """Export all compliance data as CSV for annual reporting"""
    
    detections = db.query(Detection).join(Company).outerjoin(
        CompanyResponse
    ).outerjoin(
        ComplianceReview
    ).order_by(Detection.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Assessment ID', 'Company Name', 'Timestamp', 'Risk Tier', 'Risk Score', 'Stanford CMD-1 Score',
        'Suicide Ideation', 'Planning Language', 'Isolation Markers', 'Boundary Concerns',
        'User Message Summary', 'Bot Message Summary',
        'Response Received', 'Response Time (minutes)', 'Crisis Resources Displayed', 
        'Resources Acknowledged', 'Outcome Category',
        'Review Status', 'Reviewer Name', 'Response Appropriate', 'Resources Adequate', 
        'Timing Acceptable', 'Protocol Followed', 'Reviewer Notes',
        'Created Date', 'Reporting Deadline'
    ])
    
    for detection in detections:
        response = detection.response
        review = detection.review
        
        user_msg = detection.user_message[:100] if detection.user_message else ''
        bot_msg = detection.bot_message[:100] if detection.bot_message else ''
        
        writer.writerow([
            detection.assessment_id,
            detection.company.name,
            detection.timestamp.isoformat() if detection.timestamp else '',
            detection.risk_tier,
            detection.risk_score,
            f"{detection.stanford_cmd1_score:.2f}" if detection.stanford_cmd1_score else '',
            'Yes' if detection.suicide_ideation else 'No',
            'Yes' if detection.planning_language else 'No',
            'Yes' if detection.isolation_markers else 'No',
            ', '.join(detection.boundary_concerns or []),
            user_msg,
            bot_msg,
            'Yes' if response else 'No',
            response.response_time_minutes if response else '',
            'Yes' if (response and response.crisis_resources_displayed) else 'No',
            'Yes' if (response and response.user_acknowledged_resources) else 'No',
            response.outcome_category if response else '',
            review.status if review else 'pending',
            review.reviewer_name if review else '',
            'Yes' if (review and review.response_appropriate) else 'No',
            'Yes' if (review and review.resources_adequate) else 'No',
            'Yes' if (review and review.timing_acceptable) else 'No',
            'Yes' if (review and review.protocol_followed) else 'No',
            review.reviewer_notes if review else '',
            detection.created_at.isoformat() if detection.created_at else '',
            detection.reporting_deadline.isoformat() if detection.reporting_deadline else ''
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=verus-compliance-report-{datetime.utcnow().strftime('%Y-%m-%d')}.csv"}
    )


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("dashboard.html", {"request": request})
