#!/usr/bin/env python
"""Async script to populate food_nutrient table from XLSX file.

This script reads data from the Food_Nutrient_Details.xlsx file and inserts
it into the food_nutrient table in the database using async operations.

Example usage:
    python -m scripts.python.async_populate_food_nutrient

Dependencies:
    - pandas
    - sqlalchemy
    - openpyxl
    - asyncpg
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.app.core.config import settings  # noqa: E402
from src.app.core.db.async_session import get_async_session  # noqa: E402
from src.app.core.logger import get_logger  # noqa: E402
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
    # Log all columns in the Excel file
    logger.info(f"Columns in Excel file: {list(df.columns)}")

    # Drop the "Food ID" and "Survey ID" columns if they exist
    columns_to_drop = ["Food ID", "Survey ID"]
    for col in columns_to_drop:
        if col in df.columns:
            df = df.drop(columns=[col])
            logger.info(f"Dropped column: {col}")
        else:
            logger.warning(f"Column '{col}' not found in Excel file, could not drop it")

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

    # Identify text and numeric columns
    text_columns = ["food_name", "food_category", "food_detail"]
    numeric_columns = [col for col in renamed_df.columns if col not in text_columns]

    # Handle text columns - convert to lowercase and replace NaN with None
    for col in text_columns:
        if col in renamed_df.columns:
            # First convert NaN to empty string to avoid error when calling str.lower()
            renamed_df[col] = renamed_df[col].fillna("")
            # Then convert to lowercase
            renamed_df[col] = renamed_df[col].str.lower()
            # Replace empty string back to None
            renamed_df[col] = renamed_df[col].replace("", None)
            logger.info(f"Converted {col} to lowercase and handled NaN values")

    # Handle numeric columns - convert to appropriate numeric type and NaN to None
    for col in numeric_columns:
        if col in renamed_df.columns:
            renamed_df[col] = pd.to_numeric(renamed_df[col], errors="coerce")
            # Replace NaN with None for proper SQL NULL values
            renamed_df[col] = renamed_df[col].where(pd.notna(renamed_df[col]), None)

    # Convert DataFrame to list of dictionaries
    rows = renamed_df.to_dict(orient="records")
    logger.info(f"Transformed {len(rows)} rows of data")

    return rows


def validate_row(row: Dict, index: int) -> bool:
    """Validate a row before insertion.

    Args:
        row: The row data to validate
        index: The index of the row for error reporting

    Returns:
        True if valid, False otherwise
    """
    # Check for any NaN values that might have been missed
    for key, value in row.items():
        if pd.isna(value):
            logger.error(
                f"Row {index}: Field '{key}' has NaN value. All NaN values should be converted to None."
            )
            return False

    # Check required fields
    if not row.get("food_name"):
        logger.error(f"Row {index}: Missing required field 'food_name'")
        return False

    # Validate string fields
    string_fields = ["food_name", "food_category", "food_detail"]
    for field in string_fields:
        if field in row and row[field] is not None and not isinstance(row[field], str):
            logger.error(
                f"Row {index}: Field '{field}' should be a string, got {type(row[field])}"
            )
            return False

    # Validate float fields
    float_fields = [key for key in row.keys() if key not in string_fields]
    for field in float_fields:
        if (
            field in row
            and row[field] is not None
            and not isinstance(row[field], (int, float))
        ):
            logger.error(
                f"Row {index}: Field '{field}' should be a number, got {type(row[field])}"
            )
            return False

    return True


async def insert_data(data: List[Dict], batch_size: int = 100) -> int:
    """Insert data into the food_nutrient table using async operations.

    Args:
        data: List of dictionaries containing the data to insert.
        batch_size: Number of rows to insert in each batch.

    Returns:
        Number of rows inserted.
    """
    inserted_count = 0
    failed_batches = 0
    max_failed_batches = 3  # Stop after 3 consecutive failed batches

    # Process in batches to avoid memory issues with large datasets
    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]
        logger.info(
            f"Processing batch {i//batch_size + 1} of {(len(data) + batch_size - 1) // batch_size} ({len(batch)} rows)"
        )

        batch_inserted = await insert_batch(batch)

        if batch_inserted == 0:  # Error occurred
            failed_batches += 1
            logger.warning(
                f"Batch {i//batch_size + 1} failed. Failed batches: {failed_batches}/{max_failed_batches}"
            )
            if failed_batches >= max_failed_batches:
                logger.error(
                    f"Reached maximum failed batches ({max_failed_batches}). Stopping import."
                )
                break
        else:
            # Reset failed batches count if a batch succeeds
            failed_batches = 0
            inserted_count += batch_inserted
            logger.info(
                f"Committed batch. Total rows inserted so far: {inserted_count}"
            )

    if inserted_count > 0:
        logger.info(f"Successfully inserted {inserted_count} rows")
    else:
        logger.error("No rows were inserted. Check logs for errors.")

    return inserted_count


async def insert_batch(batch: List[Dict]) -> int:
    """Insert a batch of data into the food_nutrient table using async session.

    Args:
        batch: List of dictionaries containing the data to insert.

    Returns:
        Number of rows inserted in this batch.
    """
    batch_inserted = 0

    # Validate all rows before attempting to insert
    validated_batch = []
    for i, row in enumerate(batch):
        if validate_row(row, i):
            validated_batch.append(row)
        else:
            logger.warning(f"Skipping invalid row at index {i}")

    if not validated_batch:
        logger.error("No valid rows to insert in this batch")
        return 0

    logger.info(f"Validated {len(validated_batch)} of {len(batch)} rows")

    async with get_async_session() as session:
        try:
            # Begin a transaction
            async with session.begin():
                for i, row in enumerate(validated_batch):
                    try:
                        # Create a new FoodNutrient object
                        food_nutrient = FoodNutrient()

                        # Set attributes dynamically
                        for key, value in row.items():
                            if hasattr(food_nutrient, key):
                                setattr(food_nutrient, key, value)

                        # Add to session
                        session.add(food_nutrient)
                        batch_inserted += 1
                    except Exception as row_error:
                        # Log which row failed and why, but continue with other rows
                        logger.error(f"Error inserting row {i}: {row_error}")
                        logger.debug(f"Problem row: {row}")
                        raise  # Re-raise to trigger the outer exception handler for transaction rollback

            # Session is committed automatically when exiting the context
            logger.info(f"Successfully inserted batch of {batch_inserted} rows")
        except Exception as e:
            logger.error(f"Error inserting batch: {str(e)}")
            # Add more detailed diagnostics
            if "DataError" in str(e) and "nan" in str(e):
                logger.error(
                    "NaN values detected in the data. Make sure all NaN values are properly converted to None."
                )

            # Session is rolled back automatically on exception
            batch_inserted = 0

    return batch_inserted


async def main(
    excel_path: Optional[str] = None,
    database_url: Optional[str] = None,
    batch_size: int = 100,
):
    """Main function to execute the data import process asynchronously.

    Args:
        excel_path: Path to the Excel file. If None, uses default path.
        database_url: Database URL. If None, uses settings.DATABASE_URI.
        batch_size: Number of rows to insert in each batch.
    """
    # Default excel path is at the project root
    if excel_path is None:
        excel_path = os.path.join(project_root, "Food_Nutrient_Details.xlsx")

    # Check if file exists
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found at {excel_path}")
        return

    # Override database URL in settings if provided
    if database_url:
        settings.DATABASE_URL = database_url

    # Validate batch size
    if batch_size <= 0:
        logger.warning(f"Invalid batch_size ({batch_size}), using default of 100")
        batch_size = 100

    # Read data from Excel (this is a synchronous operation)
    logger.info(f"Reading Excel file: {excel_path}")
    df = read_excel_file(excel_path)
    if df is None:
        return

    # Transform data (this is a synchronous operation)
    logger.info("Transforming data...")
    transformed_data = transform_data(df)
    if not transformed_data:
        logger.error("No data to insert after transformation")
        return

    logger.info(f"Prepared {len(transformed_data)} rows for insertion")
    logger.info(f"Using batch size of {batch_size}")

    try:
        # Insert data (this is an asynchronous operation)
        inserted_count = await insert_data(transformed_data, batch_size)
        logger.info(f"Data import completed. Inserted {inserted_count} records.")
    except Exception as e:
        logger.error(f"Failed to import data: {str(e)}")
        import traceback

        logger.debug(traceback.format_exc())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import data from Excel to food_nutrient table (async version)"
    )
    parser.add_argument(
        "--excel-path",
        type=str,
        help="Path to the Excel file (default: project_root/Food_Nutrient_Details.xlsx)",
    )
    parser.add_argument(
        "--database-url", type=str, help="Database URL (default: from settings)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of rows to insert in each batch (default: 100)",
    )

    args = parser.parse_args()

    asyncio.run(
        main(
            excel_path=args.excel_path,
            database_url=args.database_url,
            batch_size=args.batch_size,
        )
    )
