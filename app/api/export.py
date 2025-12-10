"""
Compliance Export API
Endpoints for triggering and downloading CSV compliance reports
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import io

from app.core.database import get_db
from app.services.export_service import ComplianceExportService

router = APIRouter()


@router.post("/annual-report")
async def export_annual_report(
    company_id: Optional[str] = Query(None, description="Optional company ID to filter by"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    export_type: str = Query("detailed", description="Type: 'detailed' or 'summary'"),
    db: Session = Depends(get_db)
):
    """
    POST endpoint to export compliance report as CSV
    
    Returns:
    - detailed: Comprehensive report with 40+ columns
    - summary: High-level metrics and statistics
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        
        # Generate appropriate report
        if export_type == "summary":
            csv_content = ComplianceExportService.export_summary_statistics(
                db=db,
                company_id=company_id,
                start_date=start_dt,
                end_date=end_dt
            )
            filename = f"verus-compliance-summary-{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
        else:
            csv_content = ComplianceExportService.export_annual_report(
                db=db,
                company_id=company_id,
                start_date=start_dt,
                end_date=end_dt,
                include_reviews=True
            )
            filename = f"verus-compliance-report-{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
        
        # Return as streaming response for download
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )


@router.get("/annual-report/{company_id}")
async def export_annual_report_by_company(
    company_id: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    export_type: str = Query("detailed", description="Type: 'detailed' or 'summary'"),
    db: Session = Depends(get_db)
):
    """
    GET endpoint to export compliance report for specific company
    
    Params:
    - company_id: Company identifier
    - start_date: Optional filter start date
    - end_date: Optional filter end date
    - export_type: 'detailed' or 'summary'
    
    Returns: CSV file download
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        
        # Generate appropriate report
        if export_type == "summary":
            csv_content = ComplianceExportService.export_summary_statistics(
                db=db,
                company_id=company_id,
                start_date=start_dt,
                end_date=end_dt
            )
            filename = f"verus-compliance-summary-{company_id}-{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
        else:
            csv_content = ComplianceExportService.export_annual_report(
                db=db,
                company_id=company_id,
                start_date=start_dt,
                end_date=end_dt,
                include_reviews=True
            )
            filename = f"verus-compliance-report-{company_id}-{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
        
        # Return as streaming response for download
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )


@router.get("/preview")
async def export_preview(
    company_id: Optional[str] = Query(None, description="Optional company ID"),
    export_type: str = Query("detailed", description="Type: 'detailed' or 'summary'"),
    db: Session = Depends(get_db)
):
    """
    Preview endpoint - returns first 10 rows of report for testing/demo
    
    Returns: CSV content as plain text (first 10 rows)
    """
    try:
        # Generate full report
        if export_type == "summary":
            csv_content = ComplianceExportService.export_summary_statistics(
                db=db,
                company_id=company_id
            )
        else:
            csv_content = ComplianceExportService.export_annual_report(
                db=db,
                company_id=company_id,
                include_reviews=True
            )
        
        # Return first 10 lines for preview
        lines = csv_content.split('\n')
        preview = '\n'.join(lines[:10])
        
        return {
            "preview": preview,
            "total_lines": len(lines),
            "export_type": export_type,
            "company_id": company_id or "all"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating preview: {str(e)}"
        )
