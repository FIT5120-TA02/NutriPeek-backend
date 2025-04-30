"""Food Category API endpoints for retrieving fun facts."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_async_db
from src.app.crud.crud_food_category_fun_facts import food_category_fun_fact_crud
from src.app.schemas.food_category import (
    FoodCategoryFunFactResponse,
    FoodCategoryFunFactsResponse,
)

router = APIRouter(prefix="/food-category", tags=["food-category"])


@router.get(
    "/fun-facts",
    response_model=FoodCategoryFunFactsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        500: {"description": "Internal server error"},
    },
    summary="Get food category fun facts",
    description="Retrieve fun facts for food categories. Returns random fun facts if no categories specified.",
)
async def get_food_category_fun_facts(
    categories: Optional[List[str]] = Query(
        None, description="List of food categories to get fun facts for"
    ),
    count: int = Query(
        5,
        ge=1,
        le=50,
        description="Number of random fun facts to return if no categories specified",
    ),
    db: AsyncSession = Depends(get_async_db),
):
    """Retrieve fun facts for food categories.

    This endpoint returns fun facts for specific food categories if provided,
    or a random selection of food category fun facts otherwise.

    Args:
        categories: Optional list of food categories to get fun facts for.
                   If not provided, random fun facts will be returned.
        count: Number of random fun facts to return if no categories specified.
               Default is 5, maximum is 50.
        db: Database session dependency

    Returns:
        List of food category fun facts

    Raises:
        HTTPException: If an error occurs during database retrieval
    """
    try:
        if categories:
            # Get fun facts for specified categories
            fun_facts = await food_category_fun_fact_crud.get_fun_facts_by_categories(
                db, categories=categories
            )
        else:
            # Get random fun facts if no categories specified
            fun_facts = await food_category_fun_fact_crud.get_random_fun_facts(
                db, count=count
            )

        return FoodCategoryFunFactsResponse(
            fun_facts=[
                FoodCategoryFunFactResponse(
                    id=fact.id,
                    category=fact.food_category,
                    fun_fact=fact.fun_fact,
                )
                for fact in fun_facts
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving food category fun facts: {str(e)}",
        )


@router.get(
    "/fun-facts/{category}",
    response_model=FoodCategoryFunFactResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Food category fun fact not found"},
        500: {"description": "Internal server error"},
    },
    summary="Get fun fact for a specific food category",
    description="Retrieve a fun fact for a specific food category",
)
async def get_food_category_fun_fact(
    category: str,
    db: AsyncSession = Depends(get_async_db),
):
    """Retrieve a fun fact for a specific food category.

    Args:
        category: Food category name
        db: Database session dependency

    Returns:
        Fun fact for the specified food category

    Raises:
        HTTPException: If the fun fact is not found or an error occurs
    """
    try:
        fun_fact = await food_category_fun_fact_crud.get_by_category(
            db, category=category
        )
        if not fun_fact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fun fact for category '{category}' not found",
            )
        return FoodCategoryFunFactResponse(
            id=fun_fact.id,
            category=fun_fact.food_category,
            fun_fact=fun_fact.fun_fact,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving food category fun fact: {str(e)}",
        )
