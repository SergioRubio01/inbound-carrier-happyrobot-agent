"""
File: search_loads.py
Description: Use case for searching available loads
Author: HappyRobot Team
Created: 2024-08-14
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.domain.entities import Load
from src.core.domain.exceptions.base import DomainException
from src.core.domain.value_objects import EquipmentType, Rate
from src.core.ports.repositories import ILoadRepository, LoadSearchCriteria


class LoadSearchException(DomainException):
    """Exception raised when load search fails."""

    pass


@dataclass
class LoadSearchRequest:
    """Request for load search."""

    equipment_type: str
    origin: Optional[Dict[str, Any]] = None
    destination: Optional[Dict[str, Any]] = None
    pickup_date_range: Optional[Dict[str, str]] = None
    minimum_rate: Optional[float] = None
    maximum_miles: Optional[int] = None
    commodity_types: Optional[List[str]] = None
    weight_range: Optional[Dict[str, int]] = None
    limit: int = 10
    sort_by: str = "rate_per_mile_desc"


@dataclass
class LoadSearchResponse:
    """Response for load search."""

    search_criteria: Dict[str, Any]
    total_matches: int
    returned_count: int
    loads: List[Dict[str, Any]]
    suggestions: Optional[Dict[str, Any]] = None
    search_timestamp: Optional[datetime] = None


class SearchLoadsUseCase:
    """Use case for searching available loads."""

    def __init__(self, load_repository: ILoadRepository):
        self.load_repository = load_repository

    async def execute(self, request: LoadSearchRequest) -> LoadSearchResponse:
        """Execute load search."""
        try:
            # Build search criteria
            criteria = self._build_search_criteria(request)

            # Execute search
            loads = await self.load_repository.search_loads(criteria)
            total_count = await self.load_repository.count_loads_by_criteria(criteria)

            # Convert loads to response format
            load_dicts = [self._load_to_dict(load) for load in loads]

            # Generate suggestions if no results
            suggestions = None
            if not loads:
                suggestions = await self._generate_suggestions(request)

            # Build search criteria summary
            search_criteria_summary = self._build_search_summary(request)

            return LoadSearchResponse(
                search_criteria=search_criteria_summary,
                total_matches=total_count,
                returned_count=len(loads),
                loads=load_dicts,
                suggestions=suggestions,
                search_timestamp=datetime.utcnow(),
            )

        except Exception as e:
            raise LoadSearchException(f"Failed to search loads: {str(e)}")

    def _build_search_criteria(self, request: LoadSearchRequest) -> LoadSearchCriteria:
        """Build search criteria from request."""
        equipment_type = EquipmentType.from_name(request.equipment_type)

        # Parse origin
        origin_state = None
        if request.origin and "state" in request.origin:
            origin_state = request.origin["state"]

        # Parse destination
        destination_state = None
        if request.destination and "state" in request.destination:
            destination_state = request.destination["state"]

        # Parse pickup date range
        pickup_date_start = None
        pickup_date_end = None
        if request.pickup_date_range:
            start_str = request.pickup_date_range.get("start")
            end_str = request.pickup_date_range.get("end")

            if start_str:
                pickup_date_start = datetime.fromisoformat(
                    start_str.replace("Z", "+00:00")
                ).date()
            if end_str:
                pickup_date_end = datetime.fromisoformat(
                    end_str.replace("Z", "+00:00")
                ).date()

        # Parse minimum rate
        minimum_rate = None
        if request.minimum_rate:
            minimum_rate = Rate.from_float(request.minimum_rate)

        # Parse weight range
        weight_min = None
        weight_max = None
        if request.weight_range:
            weight_min = request.weight_range.get("min")
            weight_max = request.weight_range.get("max")

        return LoadSearchCriteria(
            equipment_type=equipment_type,
            origin_state=origin_state,
            destination_state=destination_state,
            pickup_date_start=pickup_date_start,
            pickup_date_end=pickup_date_end,
            minimum_rate=minimum_rate,
            maximum_miles=request.maximum_miles,
            weight_min=weight_min,
            weight_max=weight_max,
            sort_by=request.sort_by,
            limit=request.limit,
        )

    def _load_to_dict(self, load: Load) -> Dict[str, Any]:
        """Convert load entity to dictionary for API response."""
        return {
            "load_id": str(load.load_id),
            "origin": (
                {
                    "city": load.origin.city,
                    "state": load.origin.state,
                    "zip": load.origin.zip_code,
                    "coordinates": (
                        {
                            "lat": load.origin.latitude,
                            "lng": load.origin.longitude,
                        }
                        if load.origin.latitude and load.origin.longitude
                        else None
                    ),
                }
                if load.origin
                else None
            ),
            "destination": (
                {
                    "city": load.destination.city,
                    "state": load.destination.state,
                    "zip": load.destination.zip_code,
                    "coordinates": (
                        {
                            "lat": load.destination.latitude,
                            "lng": load.destination.longitude,
                        }
                        if load.destination.latitude and load.destination.longitude
                        else None
                    ),
                }
                if load.destination
                else None
            ),
            "pickup_datetime": f"{load.pickup_date}T{load.pickup_time_start or '10:00:00'}Z",
            "delivery_datetime": f"{load.delivery_date}T{load.delivery_time_start or '18:00:00'}Z",
            "equipment_type": load.equipment_type.name if load.equipment_type else None,
            "loadboard_rate": (
                load.loadboard_rate.to_float() if load.loadboard_rate else 0.0
            ),
            "rate_per_mile": (
                load.rate_per_mile.to_float() if load.rate_per_mile else 0.0
            ),
            "miles": load.miles,
            "weight": load.weight,
            "commodity_type": load.commodity_type,
            "num_of_pieces": load.pieces,
            "dimensions": load.dimensions,
            "special_requirements": load.special_requirements or [],
            "broker_info": (
                {
                    "company": load.broker_company,
                    "contact_name": (
                        load.broker_contact.get("name") if load.broker_contact else None
                    ),
                    "phone": (
                        load.broker_contact.get("phone")
                        if load.broker_contact
                        else None
                    ),
                    "email": (
                        load.broker_contact.get("email")
                        if load.broker_contact
                        else None
                    ),
                }
                if load.broker_company or load.broker_contact
                else None
            ),
            "urgency": load.urgency.value,
            "created_at": load.created_at.isoformat(),
        }

    def _build_search_summary(self, request: LoadSearchRequest) -> Dict[str, Any]:
        """Build search criteria summary for response."""
        summary = {"equipment_type": request.equipment_type}

        if request.origin:
            origin_parts = []
            if request.origin.get("city"):
                origin_parts.append(request.origin["city"])
            if request.origin.get("state"):
                origin_parts.append(request.origin["state"])
            if request.origin.get("radius_miles"):
                origin_parts.append(f"({request.origin['radius_miles']} mi radius)")
            summary["origin"] = ", ".join(origin_parts)

        if request.destination:
            dest_parts = []
            if request.destination.get("city"):
                dest_parts.append(request.destination["city"])
            if request.destination.get("state"):
                dest_parts.append(request.destination["state"])
            if request.destination.get("radius_miles"):
                dest_parts.append(f"({request.destination['radius_miles']} mi radius)")
            summary["destination"] = ", ".join(dest_parts)

        return summary

    async def _generate_suggestions(self, request: LoadSearchRequest) -> Dict[str, Any]:
        """Generate suggestions when no loads are found."""
        suggestions = {
            "expand_radius": True,
            "alternative_equipment": [],
            "alternative_dates": True,
        }

        # Suggest alternative equipment types
        equipment_type = EquipmentType.from_name(request.equipment_type)
        if equipment_type.is_van_type:
            suggestions["alternative_equipment"] = ["48-foot van", "Reefer"]
        elif equipment_type.is_flatbed_type:
            suggestions["alternative_equipment"] = ["Step Deck", "RGN"]
        else:
            suggestions["alternative_equipment"] = ["53-foot van", "Flatbed"]

        return suggestions
