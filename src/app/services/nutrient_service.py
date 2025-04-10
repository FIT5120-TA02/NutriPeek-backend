"""Service for nutrient-related operations."""

from typing import Dict, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.exceptions.custom import ResourceNotFoundError
from src.app.crud.crud_daily_nutrient_intake import daily_nutrient_intake_crud
from src.app.crud.crud_food_nutrients import food_nutrient_crud
from src.app.models.food_nutrient import FoodNutrient
from src.app.schemas.nutrient import NutrientGapResponse, NutrientInfo


class NutrientService:
    """Service for nutrient-related operations.

    This service handles operations related to nutrients, including
    calculating nutritional gaps between recommended and actual intakes.
    """

    @staticmethod
    async def calculate_nutrient_gaps(
        db: AsyncSession, age: int, gender: str, ingredient_ids: List[str]
    ) -> NutrientGapResponse:
        """Calculate nutritional gaps for a child based on their profile and chosen ingredients.

        Args:
            db: Database session
            age: Age of the child
            gender: Gender of the child (boy/girl)
            ingredient_ids: List of ingredient IDs (food_nutrient.id)

        Returns:
            Nutritional gap information

        Raises:
            ResourceNotFoundError: If ingredients are not found or if there's no recommended
                intake data for the child's age and gender
        """
        # Get recommended nutrient intakes for the child's age and gender
        recommended_intakes = await daily_nutrient_intake_crud.get_by_age_and_gender(
            db, age=age, gender=gender
        )

        if not recommended_intakes:
            raise ResourceNotFoundError(
                f"No recommended nutrient intake data found for age {age} and gender {gender}"
            )

        # Get the nutritional content of the selected ingredients
        food_nutrients, missing_ingredients = (
            await NutrientService.get_food_nutrients_by_ids(db, ingredient_ids)
        )

        if missing_ingredients:
            missing_ids = ", ".join(missing_ingredients)
            raise ResourceNotFoundError(
                f"The following ingredients were not found: {missing_ids}"
            )

        # Calculate nutrient intakes from the selected ingredients
        nutrient_intakes = NutrientService.calculate_nutrient_intakes(food_nutrients)

        # Calculate gaps between recommended and actual intakes
        nutrient_gaps, missing_nutrients, excess_nutrients, total_calories = (
            NutrientService.calculate_gaps(recommended_intakes, nutrient_intakes)
        )

        return NutrientGapResponse(
            nutrient_gaps=nutrient_gaps,
            missing_nutrients=missing_nutrients,
            excess_nutrients=excess_nutrients,
            total_calories=total_calories,
        )

    @staticmethod
    async def get_food_nutrients_by_ids(
        db: AsyncSession, ingredient_ids: List[str]
    ) -> Tuple[List[FoodNutrient], List[str]]:
        """Get FoodNutrient objects for the given IDs.

        Args:
            db: Database session
            ingredient_ids: List of ingredient (FoodNutrient) IDs

        Returns:
            Tuple containing:
                - List of FoodNutrient objects
                - List of IDs that couldn't be found
        """
        found_nutrients = []
        missing_ids = []

        for ingredient_id in ingredient_ids:
            nutrient = await food_nutrient_crud.get(db, id=ingredient_id)
            if nutrient:
                found_nutrients.append(nutrient)
            else:
                missing_ids.append(ingredient_id)

        return found_nutrients, missing_ids

    @staticmethod
    def calculate_nutrient_intakes(
        food_nutrients: List[FoodNutrient],
    ) -> Dict[str, Dict[str, float]]:
        """Calculate the total nutrient intakes from the given food nutrients.

        Args:
            food_nutrients: List of FoodNutrient objects

        Returns:
            Dictionary mapping nutrient names to their intake amount and unit
        """
        # Initialize a dictionary to store nutrient intakes
        nutrient_intakes = {}

        # Define a mapping from model attributes to nutrient names
        # This maps the attribute names in the FoodNutrient model to the nutrient names used in DailyNutrientIntake
        nutrient_mapping = {
            "total_sugars_g": {"name": "Total sugars", "unit": "g"},
            "vitamin_b6_mg": {"name": "Vitamin B6", "unit": "mg"},
            "total_fat_g": {"name": "Total Fat(c)", "unit": "g"},
            "phosphorus_mg": {"name": "Phosphorus", "unit": "mg"},
            "monounsaturated_fat_g": {"name": "Monounsaturated fat", "unit": "g"},
            "calcium_mg": {"name": "Calcium", "unit": "mg"},
            "vitamin_c_mg": {"name": "Vitamin C", "unit": "mg"},
            "starch_g": {"name": "Starch", "unit": "g"},
            "riboflavin_b2_mg": {"name": "Riboflavin (B2)", "unit": "mg"},
            "dietary_fibre_g": {"name": "Dietary Fibre", "unit": "g"},
            "vitamin_b12_ug": {"name": "Vitamin B12", "unit": "μg"},
            "niacin_equivalents_mg": {"name": "Niacin equivalent", "unit": "mg"},
            "potassium_mg": {"name": "Potassium", "unit": "mg"},
            "dietary_folate_equivalents_ug": {
                "name": "Folate equivalent",
                "unit": "μg",
            },
            "vitamin_a_retinol_ug": {"name": "Preformed Vitamin A", "unit": "μg"},
            "polyunsaturated_fat_g": {"name": "Polyunsaturated fat(c)", "unit": "g"},
            "niacin_b3_mg": {"name": "Niacin (B3)", "unit": "mg"},
            "thiamin_b1_mg": {"name": "Thiamin (B1)", "unit": "mg"},
            "linoleic_acid_g": {"name": "Linoleic acid", "unit": "g"},
            "protein_g": {"name": "Protein", "unit": "g"},
            "cholesterol_mg": {"name": "Cholesterol", "unit": "mg"},
            "trans_fatty_acids_mg": {"name": "Trans fatty acids", "unit": "mg"},
            "zinc_mg": {"name": "Zinc", "unit": "mg"},
            "saturated_fat_g": {"name": "Saturated fat", "unit": "g"},
            "provitamin_a_equivalents_ug": {"name": "Pro Vitamin A", "unit": "μg"},
            "magnesium_mg": {"name": "Magnesium", "unit": "mg"},
            "iron_mg": {"name": "Iron", "unit": "mg"},
            "selenium_ug": {"name": "Selenium", "unit": "μg"},
            "vitamin_a_re_ug": {"name": "Vitamin A retinol equivalent", "unit": "μg"},
            "vitamin_e_mg": {"name": "Vitamin E", "unit": "mg"},
            "folate_natural_ug": {"name": "Folate, natural", "unit": "μg"},
            "omega3_long_chain_total_mg": {
                "name": "Total long chain omega 3 fatty acids",
                "unit": "mg",
            },
            "total_folates_ug": {"name": "Total Folates", "unit": "μg"},
            "energy_with_fibre_kj": {"name": "Energy(a)", "unit": "kJ"},
            "folic_acid_ug": {"name": "Folic acid", "unit": "μg"},
            "moisture_g": {"name": "Moisture(b)", "unit": "g"},
            "caffeine_mg": {"name": "Caffeine", "unit": "mg"},
            "alcohol_g": {"name": "Alcohol(d)", "unit": "g"},
            "sodium_mg": {"name": "Sodium(e)", "unit": "mg"},
            "alpha_linolenic_acid_g": {"name": "Alpha-Linolenic acid", "unit": "g"},
            "iodine_ug": {"name": "Iodine", "unit": "μg"},
            "carbs_with_sugar_alcohols_g": {"name": "Carbohydrate(c)", "unit": "g"},
        }

        # Sum up the nutrient values from all food nutrients
        for food in food_nutrients:
            for attr, mapping in nutrient_mapping.items():
                nutrient_name = mapping["name"]
                unit = mapping["unit"]
                value = (
                    getattr(food, attr, 0) or 0
                )  # Use 0 if the attribute doesn't exist or is None

                if nutrient_name not in nutrient_intakes:
                    nutrient_intakes[nutrient_name] = {"amount": 0, "unit": unit}

                nutrient_intakes[nutrient_name]["amount"] += value

        return nutrient_intakes

    @staticmethod
    def calculate_gaps(
        recommended_intakes: List,
        nutrient_intakes: Dict[str, Dict[str, float]],
    ) -> Tuple[Dict[str, NutrientInfo], List[str], List[str], float]:
        """Calculate gaps between recommended and actual nutrient intakes.

        Args:
            recommended_intakes: List of DailyNutrientIntake objects
            nutrient_intakes: Dictionary mapping nutrient names to their intake amount and unit

        Returns:
            Tuple containing:
                - Dictionary mapping nutrient names to their gap information
                - List of nutrients with no intake (missing)
                - List of nutrients exceeding recommended intake (excess)
                - Total calories from selected ingredients
        """
        nutrient_gaps = {}
        missing_nutrients = []
        excess_nutrients = []
        total_calories = nutrient_intakes.get("Energy(a)", {}).get("amount", 0)

        # Process each recommended nutrient
        for recommendation in recommended_intakes:
            nutrient_name = recommendation.nutrient
            recommended_amount = recommendation.intake
            unit = recommendation.unit
            category = recommendation.category

            # Get the actual intake for this nutrient
            current_intake_info = nutrient_intakes.get(
                nutrient_name, {"amount": 0, "unit": unit}
            )
            current_amount = current_intake_info["amount"]

            # Calculate the gap
            gap = recommended_amount - current_amount

            # Calculate gap as percentage of recommended intake
            gap_percentage = (
                (gap / recommended_amount * 100) if recommended_amount > 0 else 0
            )

            # Create nutrient info object
            nutrient_info = NutrientInfo(
                name=nutrient_name,
                recommended_intake=recommended_amount,
                current_intake=current_amount,
                unit=unit,
                gap=gap,
                gap_percentage=gap_percentage,
                category=category,
            )

            nutrient_gaps[nutrient_name] = nutrient_info

            # Check if the nutrient is missing or in excess
            if current_amount == 0:
                missing_nutrients.append(nutrient_name)
            elif gap < 0:  # negative gap means excess
                excess_nutrients.append(nutrient_name)

        return nutrient_gaps, missing_nutrients, excess_nutrients, total_calories


# Create a singleton instance
nutrient_service = NutrientService()
