import logging

logger = logging.getLogger(__name__)

# Schema models for new endpoints

# @router.get("/health", response_model=HealthCheckResponse)
# async def get_system_health(
#     current_user: User = Depends(get_current_system_admin),
# ) -> HealthCheckResponse:
#     """
#     Get...
#     """
#     try:
#         return HealthCheckResponse(
#             status=overall_status,
#         )

#     except Exception as e:
#         logger.error(f"Error getting system health: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to get system health: {str(e)}"
#         )
