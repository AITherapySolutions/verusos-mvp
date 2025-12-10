"""
Protocol Publishing API
Generates crisis protocol documents for apps
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from app.services.protocol_generator import protocol_generator

router = APIRouter()

class ProtocolRequest(BaseModel):
    """Request to generate protocol"""
    company_name: str = Field(..., description="Name of the app/company")
    company_id: str = Field(..., description="Company identifier")
    protocol_version: str = Field(default="1.0", description="Protocol version")
    contact_email: Optional[str] = Field(None, description="Contact email")
    custom_resources: Optional[List[str]] = Field(None, description="Additional crisis resources")

class ProtocolResponse(BaseModel):
    """Generated protocol documents"""
    company_name: str
    company_id: str
    protocol_version: str
    generated_date: str
    markdown: str
    html: str
    publish_url: str

@router.post("/generate", response_model=ProtocolResponse)
async def generate_protocol(request: ProtocolRequest):
    """
    Generate crisis response protocol document
    
    Returns both markdown and HTML versions
    Apps can publish to their website
    """
    
    try:
        protocol = protocol_generator.generate_protocol(
            company_name=request.company_name,
            company_id=request.company_id,
            protocol_version=request.protocol_version,
            contact_email=request.contact_email,
            custom_resources=request.custom_resources
        )
        
        return protocol
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Protocol generation error: {str(e)}"
        )

@router.get("/preview/{company_id}")
async def preview_protocol(company_id: str):
    """
    Preview protocol HTML for a company
    Returns rendered HTML
    """
    
    protocol = protocol_generator.generate_protocol(
        company_name="Demo Company",
        company_id=company_id,
        protocol_version="1.0"
    )
    
    return {"html": protocol['html']}
