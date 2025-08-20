"""
File: models.py
Description: FMCSA API response models and data structures
Author: HappyRobot Team
Created: 2024-11-15
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class FMCSACarrierInfo(BaseModel):
    """FMCSA Carrier basic information model."""

    mc_number: str = Field(..., description="Motor Carrier number")
    legal_name: str = Field(..., description="Legal business name")
    dba_name: Optional[str] = Field(None, description="Doing business as name")
    entity_type: str = Field(..., description="Type of entity (CARRIER, BROKER, etc.)")
    operating_status: str = Field(..., description="Operating status")
    physical_address: Optional[str] = Field(None, description="Physical address")
    mailing_address: Optional[str] = Field(None, description="Mailing address")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    out_of_service_date: Optional[str] = Field(None, description="Out of service date")
    mcs_150_date: Optional[str] = Field(None, description="MCS-150 form filing date")
    mcs_150_mileage: Optional[int] = Field(None, description="Mileage from MCS-150")
    power_units: Optional[int] = Field(None, description="Number of power units")
    drivers: Optional[int] = Field(None, description="Number of drivers")


class FMCSAInsuranceInfo(BaseModel):
    """FMCSA Insurance information model."""

    bipd_required: Optional[int] = Field(None, description="Required BIPD coverage")
    bipd_on_file: Optional[int] = Field(None, description="BIPD coverage on file")
    cargo_required: Optional[int] = Field(None, description="Required cargo coverage")
    cargo_on_file: Optional[int] = Field(None, description="Cargo coverage on file")
    bond_required: Optional[int] = Field(None, description="Required bond amount")
    bond_on_file: Optional[int] = Field(None, description="Bond amount on file")


class FMCSASafetyScores(BaseModel):
    """FMCSA Safety scores model."""

    unsafe_driving: Optional[float] = Field(None, description="Unsafe driving BASIC score")
    hours_of_service: Optional[float] = Field(None, description="Hours of service BASIC score")
    vehicle_maintenance: Optional[float] = Field(None, description="Vehicle maintenance BASIC score")
    controlled_substances: Optional[float] = Field(None, description="Controlled substances BASIC score")
    hazmat: Optional[float] = Field(None, description="Hazmat BASIC score")
    driver_fitness: Optional[float] = Field(None, description="Driver fitness BASIC score")
    crash_indicator: Optional[float] = Field(None, description="Crash indicator BASIC score")
    safety_rating: Optional[str] = Field(None, description="Overall safety rating")
    rating_date: Optional[str] = Field(None, description="Safety rating date")


class FMCSACarrierSnapshot(BaseModel):
    """Complete FMCSA carrier snapshot model."""

    carrier_info: FMCSACarrierInfo
    insurance_info: Optional[FMCSAInsuranceInfo] = None
    safety_scores: Optional[FMCSASafetyScores] = None
    verification_timestamp: str = Field(..., description="Timestamp when data was retrieved")
    data_source: str = Field(default="FMCSA_API", description="Source of the data")


class FMCSAAPIResponse(BaseModel):
    """Generic FMCSA API response wrapper."""

    success: bool = Field(..., description="Whether the API call was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    cached: bool = Field(default=False, description="Whether the response was cached")


class FMCSAVerificationResult(BaseModel):
    """Result of carrier verification process."""

    mc_number: str = Field(..., description="Motor Carrier number")
    eligible: bool = Field(..., description="Whether carrier is eligible")
    carrier_info: Optional[FMCSACarrierInfo] = None
    safety_scores: Optional[FMCSASafetyScores] = None
    insurance_info: Optional[FMCSAInsuranceInfo] = None
    verification_source: str = Field(..., description="Source of verification data")
    cached: bool = Field(default=False, description="Whether data was cached")
    verification_timestamp: str = Field(..., description="Verification timestamp")
    warning: Optional[str] = Field(None, description="Warning message if any")
    reason: Optional[str] = Field(None, description="Reason for eligibility status")
    details: Optional[str] = Field(None, description="Additional details")
