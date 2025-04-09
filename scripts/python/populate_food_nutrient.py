#!/usr/bin/env python
"""Script to populate food_nutrient table from XLSX file.

This script reads data from the Food_Nutrient_Details.xlsx file and inserts
it into the food_nutrient table in the database.

Example usage:
    python -m scripts.python.populate_food_nutrient

Dependencies:
    - pandas
    - sqlalchemy
    - openpyxl
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.app.core.config import settings  # noqa: E402
from src.app.core.logger import get_logger  # noqa: E402
from src.app.core.session import db_manager  # noqa: E402
from src.app.models.food_nutrient import FoodNutrient  # noqa: E402

# Configure logger
logger = get_logger(__name__)


def read_excel_file(file_path: str) -> Optional[pd.DataFrame]:
    """Read data from an Excel file.

    Args:
        file_path: Path to the Excel file.

    Returns:
        A pandas DataFrame containing the Excel data or None if reading failed.
    """
    try:
        df = pd.read_excel(file_path)
        logger.info(f"Successfully read data from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error reading Excel file {file_path}: {e}")
        return None


def transform_data(df: pd.DataFrame) -> List[Dict]:
    """Transform the Excel data into a format suitable for database insertion.

    Args:
        df: The pandas DataFrame containing the data.

    Returns:
        A list of dictionaries representing rows for the food_nutrient table.
    """
    # Map Excel columns to model fields
    # This mapping should be adjusted based on the actual Excel column names
    column_mapping = {
        "Food Name": "food_name",
        "Food Category": "food_category",
        "Food Detail": "food_detail",
        "Energy, with dietary fibre (kJ)": "energy_with_fibre_kj",
        "Energy, without dietary fibre (kJ)": "energy_without_fibre_kj",
        "Moisture (g)": "moisture_g",
        "Protein (g)": "protein_g",
        "Total fat (g)": "total_fat_g",
        "Carbohydrate, with sugar alcohols (g)": "carbs_with_sugar_alcohols_g",
        "Carbohydrate, without sugar alcohols (g)": "carbs_without_sugar_alcohols_g",
        "Starch (g)": "starch_g",
        "Total sugars (g)": "total_sugars_g",
        "Added sugars (g)": "added_sugars_g",
        "Free sugars (g)": "free_sugars_g",
        "Dietary fibre (g)": "dietary_fibre_g",
        "Alcohol (g)": "alcohol_g",
        "Ash (g)": "ash_g",
        "Vitamin A (retinol) (µg)": "vitamin_a_retinol_ug",
        "Beta-carotene (µg)": "beta_carotene_ug",
        "Provitamin A (b-carotene equivalents) (µg)": "provitamin_a_equivalents_ug",
        "Vitamin A retinol equivalents (µg)": "vitamin_a_re_ug",
        "Thiamin (B1) (mg)": "thiamin_b1_mg",
        "Riboflavin (B2) (mg)": "riboflavin_b2_mg",
        "Niacin (B3) (mg)": "niacin_b3_mg",
        "Niacin equivalents (mg)": "niacin_equivalents_mg",
        "Folate, natural (µg)": "folate_natural_ug",
        "Folic acid (µg)": "folic_acid_ug",
        "Total folates (µg)": "total_folates_ug",
        "Dietary folate equivalents (µg)": "dietary_folate_equivalents_ug",
        "Vitamin B6 (mg)": "vitamin_b6_mg",
        "Vitamin B12 (µg)": "vitamin_b12_ug",
        "Vitamin C (mg)": "vitamin_c_mg",
        "Alpha-tocopherol (mg)": "alpha_tocopherol_mg",
        "Vitamin E (mg)": "vitamin_e_mg",
        "Calcium (mg)": "calcium_mg",
        "Iodine (µg)": "iodine_ug",
        "Iron (mg)": "iron_mg",
        "Magnesium (mg)": "magnesium_mg",
        "Phosphorus (mg)": "phosphorus_mg",
        "Potassium (mg)": "potassium_mg",
        "Selenium (µg)": "selenium_ug",
        "Sodium (mg)": "sodium_mg",
        "Zinc (mg)": "zinc_mg",
        "Caffeine (mg)": "caffeine_mg",
        "Cholesterol (mg)": "cholesterol_mg",
        "Tryptophan (mg)": "tryptophan_mg",
        "Saturated fat (g)": "saturated_fat_g",
        "Monounsaturated fat (g)": "monounsaturated_fat_g",
        "Polyunsaturated fat (g)": "polyunsaturated_fat_g",
        "Linoleic acid (g)": "linoleic_acid_g",
        "Alpha-linolenic acid (g)": "alpha_linolenic_acid_g",
        "C20:5w3 Eicosapentaenoic (mg)": "epa_c20_5w3_mg",
        "C22:5w3 Docosapentaenoic (mg)": "dpa_c22_5w3_mg",
        "C22:6w3 Docosahexaenoic (mg)": "dha_c22_6w3_mg",
        "Omega 3 LC (mg)": "omega3_long_chain_total_mg",
        "Trans fatty acids (mg)": "trans_fatty_acids_mg",
    }

    # Verify required columns
    required_column = "food_name"

    # Rename columns based on mapping
    renamed_df = df.rename(columns=column_mapping)

    # Check if required column exists after renaming
    if required_column not in renamed_df.columns:
        logger.error(f"Required column '{required_column}' not found in Excel file")
        return []

    # Handle potential NaN values and convert to appropriate types
    # Convert numeric columns to float
    numeric_columns = [
        col
        for col in renamed_df.columns
        if col != "food_name" and col != "food_category" and col != "food_detail"
    ]

    for col in numeric_columns:
        if col in renamed_df.columns:
            renamed_df[col] = pd.to_numeric(renamed_df[col], errors="coerce")

    # Convert DataFrame to list of dictionaries
    rows = renamed_df.to_dict(orient="records")
    logger.info(f"Transformed {len(rows)} rows of data")

    return rows


def insert_data(data: List[Dict]) -> int:
    """Insert data into the food_nutrient table.

    Args:
        data: List of dictionaries containing the data to insert.

    Returns:
        Number of rows inserted.
    """
    inserted_count = 0
    batch_size = 100

    # Process in batches to avoid memory issues with large datasets
    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]
        batch_inserted = insert_batch(batch)

        if batch_inserted == 0:  # Error occurred
            return inserted_count

        inserted_count += batch_inserted
        logger.info(f"Committed batch. Total rows inserted so far: {inserted_count}")

    logger.info(f"Successfully inserted {inserted_count} rows")
    return inserted_count


def insert_batch(batch: List[Dict]) -> int:
    """Insert a batch of data into the food_nutrient table.

    Args:
        batch: List of dictionaries containing the data to insert.

    Returns:
        Number of rows inserted in this batch.
    """
    batch_inserted = 0

    with db_manager.session() as session:
        try:
            # Begin a transaction
            session.begin()

            for row in batch:
                # Create a new FoodNutrient object
                # Only include keys that exist in the model
                food_nutrient = FoodNutrient()

                # Set attributes dynamically
                for key, value in row.items():
                    if hasattr(food_nutrient, key):
                        setattr(food_nutrient, key, value)

                # Add to session
                session.add(food_nutrient)
                batch_inserted += 1

            # Commit the batch
            session.commit()

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error inserting batch: {e}")
            batch_inserted = 0

    return batch_inserted


def main(excel_path: Optional[str] = None, database_url: Optional[str] = None):
    """Main function to execute the data import process.

    Args:
        excel_path: Path to the Excel file. If None, uses default path.
        database_url: Database URL. If None, uses settings.DATABASE_URI.
    """
    # Default excel path is at the project root
    if excel_path is None:
        excel_path = os.path.join(project_root, "Food_Nutrient_Details.xlsx")

    # Check if file exists
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found at {excel_path}")
        return

    # Initialize database connection
    if database_url:
        # Override database URL in settings if provided
        settings.DATABASE_URI = database_url

    if not db_manager.initialize():
        logger.error("Failed to initialize database connection")
        return

    # Read data from Excel
    df = read_excel_file(excel_path)
    if df is None:
        return

    # Transform data
    transformed_data = transform_data(df)
    if not transformed_data:
        return

    # Insert data
    inserted_count = insert_data(transformed_data)

    logger.info(f"Data import completed. Inserted {inserted_count} records.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import data from Excel to food_nutrient table"
    )
    parser.add_argument(
        "--excel-path",
        type=str,
        help="Path to the Excel file (default: project_root/Food_Nutrient_Details.xlsx)",
    )
    parser.add_argument(
        "--database-url", type=str, help="Database URL (default: from settings)"
    )

    args = parser.parse_args()

    main(excel_path=args.excel_path, database_url=args.database_url)
