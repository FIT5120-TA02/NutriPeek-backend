"""Food Nutrient model module."""

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.db.base_class import Base, TimestampMixin, UUIDMixin


class FoodNutrient(Base, UUIDMixin, TimestampMixin):
    """Food Nutrient model for storing nutritional data of food items.

    Attributes:
        food_name: The name of the food item
        food_category: The category of the food item
        food_detail: Additional details about the food item
        energy_with_fibre_kj: Energy content with fibre in kilojoules
        energy_without_fibre_kj: Energy content without fibre in kilojoules
        moisture_g: Moisture content in grams
        protein_g: Protein content in grams
        total_fat_g: Total fat content in grams
        carbs_with_sugar_alcohols_g: Carbohydrates content with sugar alcohols in grams
        carbs_without_sugar_alcohols_g: Carbohydrates content without sugar alcohols in grams
        starch_g: Starch content in grams
        total_sugars_g: Total sugars content in grams
        added_sugars_g: Added sugars content in grams
        free_sugars_g: Free sugars content in grams
        dietary_fibre_g: Dietary fibre content in grams
        alcohol_g: Alcohol content in grams
        ash_g: Ash content in grams
        vitamin_a_retinol_ug: Vitamin A (retinol) content in micrograms
        beta_carotene_ug: Beta-carotene content in micrograms
        provitamin_a_equivalents_ug: Provitamin A equivalents in micrograms
        vitamin_a_re_ug: Vitamin A (retinol equivalents) in micrograms
        thiamin_b1_mg: Thiamin (B1) content in milligrams
        riboflavin_b2_mg: Riboflavin (B2) content in milligrams
        niacin_b3_mg: Niacin (B3) content in milligrams
        niacin_equivalents_mg: Niacin equivalents in milligrams
        folate_natural_ug: Natural folate content in micrograms
        folic_acid_ug: Folic acid content in micrograms
        total_folates_ug: Total folates content in micrograms
        dietary_folate_equivalents_ug: Dietary folate equivalents in micrograms
        vitamin_b6_mg: Vitamin B6 content in milligrams
        vitamin_b12_ug: Vitamin B12 content in micrograms
        vitamin_c_mg: Vitamin C content in milligrams
        alpha_tocopherol_mg: Alpha-tocopherol content in milligrams
        vitamin_e_mg: Vitamin E content in milligrams
        calcium_mg: Calcium content in milligrams
        iodine_ug: Iodine content in micrograms
        iron_mg: Iron content in milligrams
        magnesium_mg: Magnesium content in milligrams
        phosphorus_mg: Phosphorus content in milligrams
        potassium_mg: Potassium content in milligrams
        selenium_ug: Selenium content in micrograms
        sodium_mg: Sodium content in milligrams
        zinc_mg: Zinc content in milligrams
        caffeine_mg: Caffeine content in milligrams
        cholesterol_mg: Cholesterol content in milligrams
        tryptophan_mg: Tryptophan content in milligrams
        saturated_fat_g: Saturated fat content in grams
        monounsaturated_fat_g: Monounsaturated fat content in grams
        polyunsaturated_fat_g: Polyunsaturated fat content in grams
        linoleic_acid_g: Linoleic acid content in grams
        alpha_linolenic_acid_g: Alpha-linolenic acid content in grams
        epa_c20_5w3_mg: EPA (C20:5w3) content in milligrams
        dpa_c22_5w3_mg: DPA (C22:5w3) content in milligrams
        dha_c22_6w3_mg: DHA (C22:6w3) content in milligrams
        omega3_long_chain_total_mg: Total omega-3 long-chain content in milligrams
        trans_fatty_acids_mg: Trans fatty acids content in milligrams
        ingredient_nutrients: Relationship to the join table connecting to inventory
    """

    __tablename__ = "food_nutrient"

    food_name: Mapped[str] = mapped_column(String(255), nullable=False)
    food_category: Mapped[str] = mapped_column(String(100), nullable=True)
    food_detail: Mapped[str] = mapped_column(Text, nullable=True)
    energy_with_fibre_kj: Mapped[float] = mapped_column(Float, nullable=True)
    energy_without_fibre_kj: Mapped[float] = mapped_column(Float, nullable=True)
    moisture_g: Mapped[float] = mapped_column(Float, nullable=True)
    protein_g: Mapped[float] = mapped_column(Float, nullable=True)
    total_fat_g: Mapped[float] = mapped_column(Float, nullable=True)
    carbs_with_sugar_alcohols_g: Mapped[float] = mapped_column(Float, nullable=True)
    carbs_without_sugar_alcohols_g: Mapped[float] = mapped_column(Float, nullable=True)
    starch_g: Mapped[float] = mapped_column(Float, nullable=True)
    total_sugars_g: Mapped[float] = mapped_column(Float, nullable=True)
    added_sugars_g: Mapped[float] = mapped_column(Float, nullable=True)
    free_sugars_g: Mapped[float] = mapped_column(Float, nullable=True)
    dietary_fibre_g: Mapped[float] = mapped_column(Float, nullable=True)
    alcohol_g: Mapped[float] = mapped_column(Float, nullable=True)
    ash_g: Mapped[float] = mapped_column(Float, nullable=True)
    vitamin_a_retinol_ug: Mapped[float] = mapped_column(Float, nullable=True)
    beta_carotene_ug: Mapped[float] = mapped_column(Float, nullable=True)
    provitamin_a_equivalents_ug: Mapped[float] = mapped_column(Float, nullable=True)
    vitamin_a_re_ug: Mapped[float] = mapped_column(Float, nullable=True)
    thiamin_b1_mg: Mapped[float] = mapped_column(Float, nullable=True)
    riboflavin_b2_mg: Mapped[float] = mapped_column(Float, nullable=True)
    niacin_b3_mg: Mapped[float] = mapped_column(Float, nullable=True)
    niacin_equivalents_mg: Mapped[float] = mapped_column(Float, nullable=True)
    folate_natural_ug: Mapped[float] = mapped_column(Float, nullable=True)
    folic_acid_ug: Mapped[float] = mapped_column(Float, nullable=True)
    total_folates_ug: Mapped[float] = mapped_column(Float, nullable=True)
    dietary_folate_equivalents_ug: Mapped[float] = mapped_column(Float, nullable=True)
    vitamin_b6_mg: Mapped[float] = mapped_column(Float, nullable=True)
    vitamin_b12_ug: Mapped[float] = mapped_column(Float, nullable=True)
    vitamin_c_mg: Mapped[float] = mapped_column(Float, nullable=True)
    alpha_tocopherol_mg: Mapped[float] = mapped_column(Float, nullable=True)
    vitamin_e_mg: Mapped[float] = mapped_column(Float, nullable=True)
    calcium_mg: Mapped[float] = mapped_column(Float, nullable=True)
    iodine_ug: Mapped[float] = mapped_column(Float, nullable=True)
    iron_mg: Mapped[float] = mapped_column(Float, nullable=True)
    magnesium_mg: Mapped[float] = mapped_column(Float, nullable=True)
    phosphorus_mg: Mapped[float] = mapped_column(Float, nullable=True)
    potassium_mg: Mapped[float] = mapped_column(Float, nullable=True)
    selenium_ug: Mapped[float] = mapped_column(Float, nullable=True)
    sodium_mg: Mapped[float] = mapped_column(Float, nullable=True)
    zinc_mg: Mapped[float] = mapped_column(Float, nullable=True)
    caffeine_mg: Mapped[float] = mapped_column(Float, nullable=True)
    cholesterol_mg: Mapped[float] = mapped_column(Float, nullable=True)
    tryptophan_mg: Mapped[float] = mapped_column(Float, nullable=True)
    saturated_fat_g: Mapped[float] = mapped_column(Float, nullable=True)
    monounsaturated_fat_g: Mapped[float] = mapped_column(Float, nullable=True)
    polyunsaturated_fat_g: Mapped[float] = mapped_column(Float, nullable=True)
    linoleic_acid_g: Mapped[float] = mapped_column(Float, nullable=True)
    alpha_linolenic_acid_g: Mapped[float] = mapped_column(Float, nullable=True)
    epa_c20_5w3_mg: Mapped[float] = mapped_column(Float, nullable=True)
    dpa_c22_5w3_mg: Mapped[float] = mapped_column(Float, nullable=True)
    dha_c22_6w3_mg: Mapped[float] = mapped_column(Float, nullable=True)
    omega3_long_chain_total_mg: Mapped[float] = mapped_column(Float, nullable=True)
    trans_fatty_acids_mg: Mapped[float] = mapped_column(Float, nullable=True)

    # Relationships
    ingredient_nutrients = relationship(
        "IngredientNutrient",
        back_populates="food_nutrient",
        cascade="all, delete-orphan",
    )
