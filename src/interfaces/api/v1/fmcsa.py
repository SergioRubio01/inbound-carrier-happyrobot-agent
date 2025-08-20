"""
File: fmcsa.py
Description: FMCSA carrier verification API endpoints with integrated FMCSA API
Author: HappyRobot Team
Created: 2024-08-14
Updated: 2024-11-15 - Added FMCSA API integration
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

# Database dependencies
from src.interfaces.api.v1.dependencies.database import get_database_session
from src.interfaces.api.v1.dependencies.services import create_carrier_verification_service
from src.infrastructure.external_services.fmcsa.exceptions import FMCSAAuthenticationError

router = APIRouter(prefix="/fmcsa", tags=["FMCSA"])


class VerifyCarrierRequestModel(BaseModel):
    """Request model for carrier verification."""
    mc_number: str


class VerifyCarrierResponseModel(BaseModel):
    """Response model for carrier verification."""
    mc_number: str
    eligible: bool
    carrier_info: Optional[Dict[str, Any]] = None
    insurance_info: Optional[Dict[str, Any]] = None
    verification_source: str
    cached: bool = False
    verification_timestamp: str
    warning: Optional[str] = None
    reason: Optional[str] = None
    details: Optional[str] = None


@router.post("/verify", response_model=VerifyCarrierResponseModel)
async def verify_carrier(
    request: VerifyCarrierRequestModel,
    session: AsyncSession = Depends(get_database_session)
):
    """
    Verify carrier MC number and eligibility using FMCSA API with fallback.

    This endpoint verifies a carrier's Motor Carrier (MC) number using:
    1. Cache lookup for recent data
    2. FMCSA API for real-time verification
    3. Database fallback if API is unavailable

    The response includes the data source and any warnings about data freshness.
    """
    try:
        # Create the carrier verification service
        verification_service = create_carrier_verification_service(session)

        # Use the carrier verification service
        result = await verification_service.verify_carrier(
            mc_number=request.mc_number
        )

        return VerifyCarrierResponseModel(**result)

    except FMCSAAuthenticationError as e:
        raise HTTPException(
            status_code=503,
            detail=f"FMCSA service authentication failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/snapshot/{mc_number}", response_model=Dict[str, Any])
async def get_carrier_snapshot(
    mc_number: str,
    session: AsyncSession = Depends(get_database_session)
):
    """
    Get comprehensive carrier snapshot with all available data.

    This endpoint retrieves a complete snapshot of carrier information including:
    - Basic carrier information
    - Safety scores and ratings
    - Insurance coverage details
    - Operating status and compliance data
    """
    try:
        verification_service = create_carrier_verification_service(session)
        result = await verification_service.get_carrier_snapshot(mc_number)
        return result

    except FMCSAAuthenticationError as e:
        raise HTTPException(
            status_code=503,
            detail=f"FMCSA service authentication failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
async def check_fmcsa_health(
    session: AsyncSession = Depends(get_database_session)
):
    """
    Check health status of FMCSA verification services.

    Returns the health status of:
    - FMCSA API connectivity
    - Cache service availability
    - Database connectivity
    """
    try:
        verification_service = create_carrier_verification_service(session)
        health_status = await verification_service.check_service_health()

        # Return health status directly (status code is handled at API level)
        return health_status

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.delete("/cache/{mc_number}")
async def invalidate_carrier_cache(
    mc_number: str,
    session: AsyncSession = Depends(get_database_session)
):
    """
    Invalidate cached data for a specific carrier.

    Forces fresh data retrieval from FMCSA API on next verification request.
    Useful when carrier information has been updated and cache needs refreshing.
    """
    try:
        verification_service = create_carrier_verification_service(session)
        success = await verification_service.invalidate_carrier_cache(mc_number)

        if success:
            return {
                "mc_number": mc_number,
                "cache_invalidated": True,
                "message": "Cache invalidated successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "mc_number": mc_number,
                "cache_invalidated": False,
                "message": "Failed to invalidate cache",
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache invalidation failed: {str(e)}")
