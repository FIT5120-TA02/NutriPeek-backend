"""Schemas package."""

from src.app.schemas.activity import (
    ActivitiesResponse,
    ActivityDetailResponse,
    ActivityItem,
    METyLevelResponse,
    PALCalculationRequest,
    PALCalculationResponse,
)
from src.app.schemas.child_energy_requirement import (
    ChildEnergyRequirementCreate,
    ChildEnergyRequirementInDB,
    ChildEnergyRequirementResponse,
    ChildEnergyRequirementUpdate,
    FindNearestPALRequest,
    FindNearestPALResponse,
)
from src.app.schemas.file_conversion import (
    FileConversionFormatsResponse,
    FileConversionResponse,
)
from src.app.schemas.food import (
    FoodAutocompleteResponse,
    FoodCategoriesResponse,
    FoodCategoryAvgNutrients,
    FoodNutrientResponse,
    FoodRecommendation,
)
from src.app.schemas.food_category import (
    FoodCategoryFunFactBase,
    FoodCategoryFunFactCreate,
    FoodCategoryFunFactResponse,
    FoodCategoryFunFactsResponse,
    FoodCategoryFunFactUpdate,
)
from src.app.schemas.food_detection import (
    DetectionBase,
    FoodDetectionError,
    FoodDetectionResponse,
    FoodItemDetection,
    FoodItemQuantity,
    FoodMappingRequest,
    FoodMappingResponse,
    FoodNutrientSummary,
)
from src.app.schemas.health import HealthCheckResponse
from src.app.schemas.nutrient import (
    ChildProfile,
    NutrientGapRequest,
    NutrientGapResponse,
    NutrientInfo,
    NutrientIntakeInfo,
    NutrientIntakeResponse,
)
from src.app.schemas.websocket_session import (
    CreateSessionResponse,
    FileInfo,
    FilesListResponse,
    FileTransferStatus,
    FileUploadedMessage,
    FileUploadResponse,
    JoinSessionResponse,
    MealType,
    SessionStatus,
    SessionStatusResponse,
    SessionUpdateMessage,
    WebSocketMessage,
)

__all__ = [
    # Activity schemas
    "ActivitiesResponse",
    "ActivityDetailResponse",
    "ActivityItem",
    "METyLevelResponse",
    "PALCalculationRequest",
    "PALCalculationResponse",
    # Child Energy Requirement schemas
    "ChildEnergyRequirementCreate",
    "ChildEnergyRequirementInDB",
    "ChildEnergyRequirementResponse",
    "ChildEnergyRequirementUpdate",
    "FindNearestPALRequest",
    "FindNearestPALResponse",
    # Food schemas
    "FoodAutocompleteResponse",
    "FoodCategoryAvgNutrients",
    "FoodCategoryFunFactBase",
    "FoodCategoryFunFactCreate",
    "FoodCategoryFunFactResponse",
    "FoodCategoryFunFactUpdate",
    "FoodCategoryFunFactsResponse",
    "FoodNutrientResponse",
    "FoodCategoriesResponse",
    "FoodRecommendation",
    # Food category schemas
    "FoodCategoryFunFactResponse",
    # Food detection schemas
    "DetectionBase",
    "FoodDetectionError",
    "FoodDetectionResponse",
    "FoodItemDetection",
    "FoodItemQuantity",
    "FoodMappingRequest",
    "FoodMappingResponse",
    "FoodNutrientSummary",
    # Health schemas
    "HealthCheckResponse",
    # Nutrient schemas
    "ChildProfile",
    "NutrientGapRequest",
    "NutrientInfo",
    "NutrientGapResponse",
    "NutrientIntakeInfo",
    "NutrientIntakeResponse",
    # WebSocket session schemas
    "CreateSessionResponse",
    "FilesListResponse",
    "FileUploadResponse",
    "JoinSessionResponse",
    "SessionStatusResponse",
    "FileTransferStatus",
    "SessionStatus",
    "WebSocketMessage",
    "FileUploadedMessage",
    "SessionUpdateMessage",
    "FileInfo",
    "MealType",
    # File conversion schemas
    "FileConversionFormatsResponse",
    "FileConversionResponse",
]
