"""Activity service module for physical activity calculations."""

from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crud.crud_activity_mety_levels import activity_mety_level_crud


class ActivityService:
    """Service for activity-related operations."""

    def __init__(self, db: AsyncSession):
        """Initialize ActivityService.

        Args:
            db: Database session
        """
        self.db = db

    async def get_distinct_activities(self) -> List[str]:
        """Get list of all distinct specific activities.

        Returns:
            List of activity names
        """
        return await activity_mety_level_crud.get_distinct_activities(self.db)

    async def get_mety_level(self, age: int, activity: str) -> Optional[float]:
        """Get METy level for a specific age and activity.

        If the exact age is not found, uses the closest available age.

        Args:
            age: Age of the person
            activity: Specific activity name

        Returns:
            METy level value if found, None otherwise
        """
        mety_record = await activity_mety_level_crud.get_closest_age_mety_level(
            self.db, age=age, specific_activity=activity
        )
        return mety_record.mety_level if mety_record else None

    async def calculate_physical_activity_level(
        self, age: int, activities: List[Dict[str, float]]
    ) -> Dict[str, float]:
        """Calculate Physical Activity Level (PAL) based on activities and their durations.

        PAL = Sum of (METy × duration for each activity) ÷ Total minutes in a day (1440)

        Args:
            age: Age of the person
            activities: List of dictionaries with 'name' (specific_activity) and 'hours' (duration in hours)

        Returns:
            Dictionary with 'pal' value and 'details' of the calculation

        Raises:
            HTTPException: If any activity is not found or if no activities are provided
        """
        if not activities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No activities provided",
            )

        total_mety_minutes = 0
        activity_details = []
        total_activity_hours = 0

        # Calculate METy-minutes for each activity
        for activity_item in activities:
            activity_name = activity_item.get("name")
            hours = activity_item.get("hours", 0)

            if not activity_name or hours <= 0:
                continue

            # Convert hours to minutes
            minutes = hours * 60
            total_activity_hours += hours

            # Get METy level for this activity and age
            mety_level = await self.get_mety_level(age, activity_name)
            if mety_level is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Activity '{activity_name}' not found for age {age}",
                )

            # Calculate METy-minutes for this activity
            activity_mety_minutes = mety_level * minutes
            total_mety_minutes += activity_mety_minutes

            # Add to details
            activity_details.append(
                {
                    "activity": activity_name,
                    "hours": hours,
                    "mety_level": mety_level,
                    "mety_minutes": activity_mety_minutes,
                }
            )

        # Calculate PAL
        # Total minutes in a day = 24 hours * 60 minutes = 1440 minutes
        minutes_in_day = 24 * 60
        pal = total_mety_minutes / minutes_in_day

        # For the remaining time not accounted for in activities, assume a rest METy level of 1.0
        # This is a simplified assumption - in reality, different rest activities might have different METy levels
        remaining_hours = 24 - total_activity_hours
        if remaining_hours > 0:
            rest_mety_level = 1.0  # Resting METy level
            rest_minutes = remaining_hours * 60
            rest_mety_minutes = rest_mety_level * rest_minutes

            activity_details.append(
                {
                    "activity": "Rest/Other Activities",
                    "hours": remaining_hours,
                    "mety_level": rest_mety_level,
                    "mety_minutes": rest_mety_minutes,
                }
            )

            # Update total with rest time
            total_mety_minutes += rest_mety_minutes
            pal = total_mety_minutes / minutes_in_day

        return {
            "pal": round(pal, 2),
            "total_mety_minutes": total_mety_minutes,
            "details": activity_details,
        }
