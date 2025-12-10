"""
Compliance Export Service
Generates CSV reports with all compliance data for FDA audit trails
"""

import csv
import io
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.database import Detection, CompanyResponse, ComplianceReview, Company


class ComplianceExportService:
    """Service for exporting compliance data to CSV format"""
    
    @staticmethod
    def export_annual_report(
        db: Session,
        company_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_reviews: bool = True
    ) -> str:
        """
        Export comprehensive annual compliance report with all detection and review data
        
        Returns CSV string with 40+ columns:
        - Assessment metadata (ID, timestamp, company)
        - Detection flags (suicide ideation, planning, isolation, boundaries)
        - Risk scoring (score, tier, Stanford CMD-1 score)
        - Message content (user message, bot message summaries)
        - Company response details (resources, timing, outcomes)
        - Compliance review (status, reviewer assessments, notes)
        - Timeline data (created dates, deadlines)
        """
        
        # Build query
        query = db.query(Detection).outerjoin(CompanyResponse).outerjoin(ComplianceReview)
        
        if company_id:
            query = query.filter(Detection.company_id == company_id)
        
        if start_date:
            query = query.filter(Detection.timestamp >= start_date)
        
        if end_date:
            query = query.filter(Detection.timestamp <= end_date)
        
        detections = query.all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header with 40+ columns
        headers = [
            # Assessment Metadata
            "Assessment ID",
            "Company ID",
            "Session ID",
            "User ID Hash",
            "Timestamp",
            "Detected Date",
            
            # Risk Scoring
            "Risk Score (0-100)",
            "Risk Tier (1-4)",
            "Tier Label",
            "Stanford CMD-1 Score",
            "Confidence Score",
            
            # Detection Flags
            "Suicide Ideation",
            "Planning Language",
            "Isolation Markers",
            "Boundary Concerns",
            "Temporal Pattern",
            
            # Message Content
            "User Message (Summary)",
            "Bot Response (Summary)",
            "Context for Review",
            "Recommended Actions",
            
            # Company Response
            "Response Received",
            "Response Time (Minutes)",
            "Crisis Resources Displayed",
            "Resources Shown",
            "User Acknowledged Resources",
            "User Clicked Resource",
            "Which Resource Clicked",
            "Internal Actions Taken",
            "Escalation Required",
            "Escalation Reason",
            "Outcome Category",
            "Outcome Details",
            "Follow-up Planned",
            "Protocol Followed",
            "Failure to Respond",
            "Failure Reason",
            "Additional Response Notes",
            
            # Compliance Review
            "Review Status",
            "Reviewer Name",
            "Reviewed Date",
            "Response Appropriate",
            "Resources Adequate",
            "Timing Acceptable",
            "Protocol Followed (Review)",
            "Reviewer Notes",
            
            # Timeline
            "Reporting Deadline",
            "Created At",
            "Response Received At"
        ]
        
        writer.writerow(headers)
        
        # Write data rows
        for detection in detections:
            response = detection.response
            review = detection.review if include_reviews else None
            
            row = [
                # Assessment Metadata
                detection.assessment_id,
                str(detection.company_id),
                detection.session_id,
                detection.user_id_hash,
                detection.timestamp.isoformat() if detection.timestamp else "",
                detection.timestamp.strftime("%Y-%m-%d") if detection.timestamp else "",
                
                # Risk Scoring
                detection.risk_score,
                detection.risk_tier,
                detection.tier_label,
                round(detection.stanford_cmd1_score, 3) if detection.stanford_cmd1_score else "",
                round(detection.stanford_cmd1_score, 1) if detection.stanford_cmd1_score else "",
                
                # Detection Flags
                "Yes" if detection.suicide_ideation else "No",
                "Yes" if detection.planning_language else "No",
                "Yes" if detection.isolation_markers else "No",
                json.dumps(detection.boundary_concerns) if detection.boundary_concerns else "",
                detection.temporal_pattern or "",
                
                # Message Content
                detection.user_message[:100] if detection.user_message else "",
                detection.bot_message[:100] if detection.bot_message else "",
                detection.context_for_review or "",
                json.dumps(detection.recommended_actions) if detection.recommended_actions else "",
                
                # Company Response
                "Yes" if response else "No",
                response.response_time_minutes if response else "",
                "Yes" if response and response.crisis_resources_displayed else "No",
                json.dumps(response.resources_shown) if response and response.resources_shown else "",
                "Yes" if response and response.user_acknowledged_resources else ("No" if response else ""),
                "Yes" if response and response.user_clicked_resource else ("No" if response else ""),
                response.which_resource_clicked if response else "",
                json.dumps(response.internal_actions) if response and response.internal_actions else "",
                "Yes" if response and response.escalation_required else ("No" if response else ""),
                response.escalation_reason if response else "",
                response.outcome_category if response else "",
                response.outcome_details if response else "",
                "Yes" if response and response.follow_up_planned else ("No" if response else ""),
                response.protocol_followed if response else "",
                "Yes" if response and response.failure_to_respond else ("No" if response else ""),
                response.failure_reason if response else "",
                response.additional_notes if response else "",
                
                # Compliance Review
                review.status if review else "Pending",
                review.reviewer_name if review else "",
                review.reviewed_at.isoformat() if review and review.reviewed_at else "",
                "Yes" if review and review.response_appropriate else ("No" if review else ""),
                "Yes" if review and review.resources_adequate else ("No" if review else ""),
                "Yes" if review and review.timing_acceptable else ("No" if review else ""),
                "Yes" if review and review.protocol_followed else ("No" if review else ""),
                review.reviewer_notes if review else "",
                
                # Timeline
                detection.reporting_deadline.isoformat() if detection.reporting_deadline else "",
                detection.created_at.isoformat() if detection.created_at else "",
                response.created_at.isoformat() if response else ""
            ]
            
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def export_summary_statistics(
        db: Session,
        company_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export high-level compliance statistics summary
        
        Returns CSV with:
        - Total detections by tier
        - Response time metrics
        - Compliance rates
        - Review status distribution
        """
        
        # Build query
        query = db.query(Detection)
        
        if company_id:
            query = query.filter(Detection.company_id == company_id)
        
        if start_date:
            query = query.filter(Detection.timestamp >= start_date)
        
        if end_date:
            query = query.filter(Detection.timestamp <= end_date)
        
        # Calculate statistics
        total_detections = query.count()
        
        tier_stats = {}
        for tier in [1, 2, 3, 4]:
            count = query.filter(Detection.risk_tier == tier).count()
            tier_stats[f"tier_{tier}"] = count
        
        # Response statistics
        responded = query.outerjoin(CompanyResponse).filter(
            CompanyResponse.id != None
        ).count()
        
        not_responded = total_detections - responded
        
        # Response time average
        avg_response_time = db.query(func.avg(CompanyResponse.response_time_minutes)).scalar()
        
        # Compliance review statistics
        reviews = query.outerjoin(ComplianceReview)
        
        compliant = reviews.filter(ComplianceReview.status == "approved").count()
        needs_followup = reviews.filter(ComplianceReview.status == "revision_requested").count()
        non_compliant = reviews.filter(ComplianceReview.status == "escalated").count()
        pending_reviews = reviews.filter(ComplianceReview.id == None).count()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Summary section
        writer.writerow(["VerusOS Compliance Summary Report"])
        writer.writerow(["Generated", datetime.utcnow().isoformat()])
        writer.writerow([])
        
        # Detection statistics
        writer.writerow(["Detection Statistics"])
        writer.writerow(["Total Detections", total_detections])
        writer.writerow([])
        
        writer.writerow(["Detections by Tier"])
        writer.writerow(["Tier 1 - Immediate", tier_stats["tier_1"]])
        writer.writerow(["Tier 2 - Urgent", tier_stats["tier_2"]])
        writer.writerow(["Tier 3 - Elevated", tier_stats["tier_3"]])
        writer.writerow(["Tier 4 - Baseline", tier_stats["tier_4"]])
        writer.writerow([])
        
        # Response statistics
        writer.writerow(["Response Statistics"])
        writer.writerow(["Detections Responded To", responded])
        writer.writerow(["Detections Not Responded", not_responded])
        response_rate = (responded / total_detections * 100) if total_detections > 0 else 0
        writer.writerow(["Response Rate (%)", round(response_rate, 2)])
        writer.writerow(["Average Response Time (Minutes)", round(avg_response_time, 2) if avg_response_time else "N/A"])
        writer.writerow([])
        
        # Compliance statistics
        writer.writerow(["Compliance Review Statistics"])
        writer.writerow(["Compliant", compliant])
        writer.writerow(["Needs Follow-Up", needs_followup])
        writer.writerow(["Non-Compliant", non_compliant])
        writer.writerow(["Pending Review", pending_reviews])
        
        reviewed_total = compliant + needs_followup + non_compliant
        compliance_rate = (compliant / reviewed_total * 100) if reviewed_total > 0 else 0
        writer.writerow(["Compliance Rate (%) - Reviewed Items", round(compliance_rate, 2)])
        writer.writerow([])
        
        # Risk metrics
        writer.writerow(["Risk Metrics"])
        high_risk_count = query.filter(Detection.risk_tier.in_([1, 2])).count()
        writer.writerow(["High Risk Detections (Tier 1-2)", high_risk_count])
        
        return output.getvalue()
