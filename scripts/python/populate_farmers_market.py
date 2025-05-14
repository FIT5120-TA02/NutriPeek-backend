#!/usr/bin/env python
"""Async script to populate farmers_market table from XLSX file.

This script reads data from the "Regional farmers market.xlsx" file and inserts
it into the farmers_market table in the database using async operations.
The script handles pre-processed data with separate columns for opening days,
opening hours, contact information, and website URLs.

Example usage:
    python -m scripts.python.populate_farmers_market

Dependencies:
    - pandas
    - sqlalchemy
    - openpyxl
    - asyncpg
"""

import argparse
import asyncio
import os
import re
import sys
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.app.core.config import settings  # noqa: E402
from src.app.core.db.async_session import get_async_session  # noqa: E402
from src.app.core.logger import get_logger  # noqa: E402
from src.app.models.farmers_market import DayOfWeek, FarmersMarket  # noqa: E402

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


def parse_opening_day(
    opening_days_text: str,
) -> Tuple[Optional[DayOfWeek], Optional[bool], Optional[str]]:
    """Parse opening days text into structured components.

    Args:
        opening_days_text: The opening days text (e.g., "Saturday", "Alternate Saturdays")

    Returns:
        Tuple of (day_of_week, is_recurring, frequency)
    """
    if not opening_days_text or pd.isna(opening_days_text):
        return None, None, None

    # Default values
    day_of_week = None
    is_recurring = True
    frequency = "weekly"

    # Normalize the text
    normalized_text = str(opening_days_text).lower().strip()

    # Map day names to enum
    day_mapping = {
        "monday": DayOfWeek.MONDAY,
        "mon": DayOfWeek.MONDAY,
        "tuesday": DayOfWeek.TUESDAY,
        "tues": DayOfWeek.TUESDAY,
        "tue": DayOfWeek.TUESDAY,
        "wednesday": DayOfWeek.WEDNESDAY,
        "wed": DayOfWeek.WEDNESDAY,
        "thursday": DayOfWeek.THURSDAY,
        "thurs": DayOfWeek.THURSDAY,
        "thu": DayOfWeek.THURSDAY,
        "friday": DayOfWeek.FRIDAY,
        "fri": DayOfWeek.FRIDAY,
        "saturday": DayOfWeek.SATURDAY,
        "sat": DayOfWeek.SATURDAY,
        "sunday": DayOfWeek.SUNDAY,
        "sun": DayOfWeek.SUNDAY,
    }

    # Try to extract the day
    for day_name, enum_val in day_mapping.items():
        day_pattern = re.compile(
            f"\\b{day_name}\\b|\\b{day_name}s\\b|\\b{day_name}\\.\\b", re.IGNORECASE
        )
        if day_pattern.search(normalized_text):
            day_of_week = enum_val
            break

    # Check for frequency indicators
    # First check for specific ordinals
    if re.search(r"\b(1st|first)\b", normalized_text, re.IGNORECASE):
        frequency = "monthly"
        if re.search(r"\b(3rd|third)\b", normalized_text, re.IGNORECASE) or re.search(
            r"\b(5th|fifth)\b", normalized_text, re.IGNORECASE
        ):
            frequency = "semi-monthly"  # 1st and 3rd
    elif re.search(r"\b(2nd|second)\b", normalized_text, re.IGNORECASE):
        frequency = "monthly"
        if re.search(r"\b(4th|fourth)\b", normalized_text, re.IGNORECASE):
            frequency = "semi-monthly"  # 2nd and 4th
    elif re.search(r"\b(3rd|third)\b", normalized_text, re.IGNORECASE):
        frequency = "monthly"
    elif re.search(r"\b(4th|fourth)\b", normalized_text, re.IGNORECASE):
        frequency = "monthly"
    elif re.search(r"\b(5th|fifth)\b", normalized_text, re.IGNORECASE):
        frequency = "monthly"
    elif re.search(r"\b(last)\b", normalized_text, re.IGNORECASE):
        frequency = "monthly"

    # Check for other frequency words
    if re.search(
        r"\b(alernate|alternate|every\s+other|fortnightly)\b",
        normalized_text,
        re.IGNORECASE,
    ):
        frequency = "biweekly"
    elif (
        re.search(r"\bmonthly\b", normalized_text, re.IGNORECASE)
        and frequency != "semi-monthly"
    ):
        frequency = "monthly"
    elif re.search(r"\bweekly\b", normalized_text, re.IGNORECASE):
        frequency = "weekly"
    elif re.search(
        r"\bevery\s+(day|week|sat|sun|mon|tue|wed|thu|fri)\b",
        normalized_text,
        re.IGNORECASE,
    ):
        frequency = "weekly"

    return day_of_week, is_recurring, frequency


def parse_opening_hours(hours_text: str) -> Tuple[Optional[time], Optional[time]]:
    """Parse opening hours text into opening and closing times.

    Args:
        hours_text: The opening hours text in format like "8:00 AM - 12:00 PM"

    Returns:
        Tuple of (opening_time, closing_time)
    """
    if not hours_text:
        return None, None

    # Handle case where hours_text is already a time object
    if isinstance(hours_text, time):
        # If it's already a time object, assume a 4-hour duration
        opening_time = hours_text
        closing_hour = (opening_time.hour + 4) % 24
        closing_time = time(hour=closing_hour, minute=opening_time.minute)
        return opening_time, closing_time

    # Handle case where hours_text is a datetime object
    if isinstance(hours_text, datetime):
        opening_time = hours_text.time()
        closing_hour = (opening_time.hour + 4) % 24
        closing_time = time(hour=closing_hour, minute=opening_time.minute)
        return opening_time, closing_time

    # If it's not a string, convert it to a string
    if not isinstance(hours_text, str):
        try:
            hours_text = str(hours_text)
        except Exception as e:
            logger.error(f"Failed to convert hours_text to string: {e}")
            return None, None

    # Handle pandas NaN
    if pd.isna(hours_text):
        return None, None

    # Handle special case for Excel datetime format
    if "Sat Dec 30 1899" in hours_text:
        # Try to extract just the time part
        time_match = re.search(r"(\d{2}):(\d{2}):(\d{2})", hours_text)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            # Assume market runs for 4 hours
            return time(hour=hours, minute=minutes), time(
                hour=(hours + 4) % 24, minute=minutes
            )

    # Handle common time formats with AM/PM
    time_pattern = r"(\d{1,2})(?::(\d{2}))?(?:\s*)?([AP]M)(?:\s*)?[-–](?:\s*)?(\d{1,2})(?::(\d{2}))?(?:\s*)?([AP]M)"
    time_matches = re.search(time_pattern, hours_text, re.IGNORECASE)

    if time_matches:
        try:
            # Extract opening time
            open_hour = int(time_matches.group(1))
            open_minute = int(time_matches.group(2)) if time_matches.group(2) else 0
            open_ampm = time_matches.group(3).upper()

            # Convert to 24-hour format
            if open_ampm == "PM" and open_hour < 12:
                open_hour += 12
            elif open_ampm == "AM" and open_hour == 12:
                open_hour = 0

            opening_time = time(hour=open_hour, minute=open_minute)

            # Extract closing time
            close_hour = int(time_matches.group(4))
            close_minute = int(time_matches.group(5)) if time_matches.group(5) else 0
            close_ampm = time_matches.group(6).upper()

            # Convert to 24-hour format
            if close_ampm == "PM" and close_hour < 12:
                close_hour += 12
            elif close_ampm == "AM" and close_hour == 12:
                close_hour = 0

            closing_time = time(hour=close_hour, minute=close_minute)

            return opening_time, closing_time
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing time: {hours_text}, error: {e}")

    # Handle format like "8am - noon" or "8am - 12noon"
    noon_pattern = r"(\d{1,2})(?::(\d{2}))?(?:\s*)?([ap]\.?m\.?)(?:\s*)?[-–](?:\s*)?(?:noon|12\s*noon)"
    noon_matches = re.search(noon_pattern, hours_text, re.IGNORECASE)

    if noon_matches:
        try:
            open_hour = int(noon_matches.group(1))
            open_minute = int(noon_matches.group(2)) if noon_matches.group(2) else 0
            open_ampm = noon_matches.group(3).lower()[0]

            # Convert to 24-hour format
            if open_ampm == "p" and open_hour < 12:
                open_hour += 12
            elif open_ampm == "a" and open_hour == 12:
                open_hour = 0

            opening_time = time(hour=open_hour, minute=open_minute)
            closing_time = time(hour=12, minute=0)  # noon

            return opening_time, closing_time
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing noon time: {hours_text}, error: {e}")

    # If all parsing attempts failed but we have a day, use default market hours
    return None, None


def extract_city_from_address(address: str) -> Optional[str]:
    """Extract city name from the address string.

    Args:
        address: Full address text

    Returns:
        City name if found, otherwise None
    """
    if not address or pd.isna(address):
        return None

    # Split address into parts by comma
    address_parts = address.split(",")
    if len(address_parts) >= 2:
        # Assume the last or second-to-last part contains the city
        city_part = (
            address_parts[-2].strip()
            if len(address_parts) > 2
            else address_parts[-1].strip()
        )
        # Try to extract just the city name, removing any postal codes
        city_match = re.search(r"([A-Za-z\s]+)", city_part)
        if city_match:
            return city_match.group(1).strip()

    return None


def transform_data(df: pd.DataFrame) -> List[Dict]:
    """Transform the Excel data into a format suitable for database insertion.

    Args:
        df: The pandas DataFrame containing the data.

    Returns:
        A list of dictionaries representing rows for the farmers_market table.
    """
    # Log all columns in the Excel file
    logger.info(f"Columns in Excel file: {list(df.columns)}")

    # Define the column mapping from Excel to database
    column_mapping = {
        "Farmers Market Name": "name",
        "Address": "address",
        "Opening Days": "opening_days",
        "Opening Hours": "opening_hours",
        "Farmers Market Website": "website",
        "Contact Name": "contact_name",
        "Contact Email": "email",
        "Contact Phone": "phone",
        "Region": "region",
    }

    # Verify required columns exist
    required_columns = ["Farmers Market Name", "Address", "Region"]
    for excel_col in required_columns:
        if excel_col not in df.columns:
            logger.error(f"Required column '{excel_col}' not found in Excel file")
            return []

    # Replace NaN values with None before processing
    df = df.where(pd.notna(df), None)

    # Rename columns based on mapping
    renamed_df = df.rename(columns=column_mapping)

    # Handle nulls (this should now be redundant but kept for safety)
    for col in renamed_df.columns:
        renamed_df[col] = renamed_df[col].fillna("")

    # Create the opening_hours_text by combining days and hours
    def combine_opening_info(row):
        days = str(row["opening_days"]) if row["opening_days"] is not None else ""
        hours = str(row["opening_hours"]) if row["opening_hours"] is not None else ""
        return f"{days} {hours}".strip()

    renamed_df["opening_hours_text"] = renamed_df.apply(combine_opening_info, axis=1)

    # Convert DataFrame to list of dictionaries
    rows = renamed_df.to_dict(orient="records")
    logger.info(f"Transformed {len(rows)} rows of data")

    # Process each row to add structured fields
    for i, row in enumerate(rows):
        # Trim whitespace from string fields
        for field in ["name", "address", "region", "website", "email", "phone"]:
            if row.get(field) is not None:
                row[field] = str(row[field]).strip()

        # Parse opening days into structured fields
        day_of_week, is_recurring, frequency = parse_opening_day(
            row.get("opening_days", "")
        )
        row["primary_day"] = (
            day_of_week  # Store the enum object directly, not just the value
        )
        row["is_recurring"] = is_recurring
        row["frequency"] = frequency

        # Parse opening hours into time fields
        opening_time, closing_time = parse_opening_hours(row.get("opening_hours", ""))
        row["opening_time"] = opening_time
        row["closing_time"] = closing_time

        # If we have a day but no times, set default market hours (8am-12pm)
        if day_of_week and (not opening_time or not closing_time):
            logger.info(f"Setting default hours for market: {row.get('name')}")
            row["opening_time"] = time(hour=8, minute=0)
            row["closing_time"] = time(hour=12, minute=0)

        # Extract city from address
        row["city"] = extract_city_from_address(row.get("address", ""))

        # Remove temporary fields that aren't in the model
        for field in ["opening_days", "opening_hours", "contact_name"]:
            if field in row:
                del row[field]

        # Double-check: Replace None or empty strings with None
        for key, value in row.items():
            if value is None or value == "":
                row[key] = None

    return rows

    return rows


def validate_row(row: Dict, index: int) -> bool:
    """Validate a row before insertion.

    Args:
        row: The row data to validate
        index: The index of the row for error reporting

    Returns:
        True if valid, False otherwise
    """
    # Check required fields
    required_fields = ["name", "address", "opening_hours_text", "region"]
    for field in required_fields:
        if field not in row or row.get(field) is None:
            logger.error(f"Row {index}: Missing required field '{field}'")
            return False

    return True


async def insert_data(data: List[Dict], batch_size: int = 100) -> int:
    """Insert data into the farmers_market table using async operations.

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
                f"Failed batch {i//batch_size + 1}. Consecutive failures: {failed_batches}"
            )
            if failed_batches >= max_failed_batches:
                logger.error(
                    f"Stopping after {failed_batches} consecutive failed batches"
                )
                break
        else:
            failed_batches = 0  # Reset counter on successful batch
            inserted_count += batch_inserted

    logger.info(f"Total inserted rows: {inserted_count}")
    return inserted_count


async def insert_batch(batch: List[Dict]) -> int:
    """Insert a batch of rows into the farmers_market table.

    Args:
        batch: List of dictionaries containing the data to insert.

    Returns:
        Number of rows inserted in this batch.
    """
    # Validate each row in the batch
    valid_rows = []
    for i, row in enumerate(batch):
        if validate_row(row, i):
            valid_rows.append(row)
        else:
            logger.warning(f"Skipping invalid row at index {i}")

    if not valid_rows:
        logger.error("No valid rows in batch")
        return 0

    try:
        # Get async session using context manager
        async with get_async_session() as session:
            try:
                # Create ORM objects
                orm_objects = []
                for row in valid_rows:
                    try:
                        # Create a copy of the row data to avoid modifying the original
                        row_data = row.copy()

                        # Remove any fields that are not in the model
                        model_fields = [
                            "name",
                            "address",
                            "opening_hours_text",
                            "region",
                            "city",
                            "postal_code",
                            "latitude",
                            "longitude",
                            "primary_day",
                            "is_recurring",
                            "frequency",
                            "opening_time",
                            "closing_time",
                            "website",
                            "phone",
                            "email",
                            "description",
                        ]

                        # Only keep fields that are in the model
                        filtered_row = {
                            k: v for k, v in row_data.items() if k in model_fields
                        }

                        orm_objects.append(FarmersMarket(**filtered_row))
                    except Exception as e:
                        logger.error(f"Error creating ORM object: {e}, Row data: {row}")
                        continue

                if not orm_objects:
                    logger.error("No valid ORM objects could be created")
                    return 0

                # Add all objects to session
                session.add_all(orm_objects)

                # Commit the transaction
                await session.commit()

                logger.info(f"Successfully inserted {len(orm_objects)} rows")
                return len(orm_objects)
            except Exception as e:
                await session.rollback()
                logger.error(f"Error inserting batch: {e}")
                return 0
    except Exception as e:
        logger.error(f"Error getting database session: {e}")
        return 0


async def main(
    excel_path: Optional[str] = None,
    database_url: Optional[str] = None,
    batch_size: int = 100,
):
    """Main function to run the script.

    Args:
        excel_path: Path to the Excel file. Defaults to a predefined path.
        database_url: URL for the database connection. Defaults to settings.SQLALCHEMY_DATABASE_URI.
        batch_size: Number of rows to insert in each batch. Defaults to 100.
    """
    # Default excel path is at the project root
    if excel_path is None:
        excel_path = os.path.join(project_root, "Regional farmers market.xlsx")
        logger.info(f"Using default Excel file path: {excel_path}")

    # Check if file exists
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found at {excel_path}")
        return

    # Configure database URL if provided
    if database_url:
        settings.SQLALCHEMY_DATABASE_URI = database_url
        logger.info(f"Using custom database URL: {database_url}")

    # Read and transform data
    df = read_excel_file(excel_path)
    if df is None:
        logger.error("Failed to read Excel file. Exiting.")
        return

    data = transform_data(df)
    if not data:
        logger.error("Failed to transform data. Exiting.")
        return

    # Insert data into database
    inserted_count = await insert_data(data, batch_size)
    logger.info(
        f"Script completed. Inserted {inserted_count} rows out of {len(data)} total rows."
    )


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Populate farmers_market table from Excel file"
    )
    parser.add_argument(
        "--excel-path",
        help="Path to the Excel file (default: project_root/Regional farmers market.xlsx)",
        default=None,
    )
    parser.add_argument(
        "--database-url", help="Database URL (default: from settings)", default=None
    )
    parser.add_argument(
        "--batch-size",
        help="Batch size for database insertions (default: 200)",
        type=int,
        default=200,
    )
    args = parser.parse_args()

    # Run the async main function
    asyncio.run(
        main(
            excel_path=args.excel_path,
            database_url=args.database_url,
            batch_size=args.batch_size,
        )
    )
