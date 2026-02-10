"""Pydantic validators for complex tool inputs."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class KeywordInput(BaseModel):
    """Validated keyword input for add_keywords."""

    text: str = Field(..., min_length=1, max_length=80, description="Keyword text")
    match_type: str = Field(default="BROAD", description="EXACT, PHRASE, or BROAD")

    @field_validator("match_type")
    @classmethod
    def validate_match_type(cls, v: str) -> str:
        valid = {"EXACT", "PHRASE", "BROAD"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"match_type must be one of {valid}, got '{v}'")
        return upper


class SitelinkInput(BaseModel):
    """Validated sitelink input for create_sitelink_assets."""

    link_text: str = Field(..., min_length=1, max_length=25, description="Sitelink text")
    final_url: str = Field(..., min_length=1, description="Landing page URL")
    description1: str | None = Field(default=None, max_length=35, description="First description line")
    description2: str | None = Field(default=None, max_length=35, description="Second description line")

    @field_validator("final_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"final_url must start with http:// or https://, got '{v}'")
        return v


class ConversionInput(BaseModel):
    """Validated offline conversion input for import_offline_conversions."""

    gclid: str = Field(..., min_length=1, description="Google Click ID")
    conversion_action_id: str = Field(..., min_length=1, description="Conversion action ID")
    conversion_date_time: str = Field(
        ...,
        min_length=1,
        description="Conversion datetime (yyyy-mm-dd hh:mm:ss+|-hh:mm)",
    )
    conversion_value: float | None = Field(default=None, ge=0, description="Conversion value")


class PriceItemInput(BaseModel):
    """Validated price item input for create_price_asset."""

    header: str = Field(..., min_length=1, max_length=25, description="Price item header")
    description: str = Field(..., min_length=1, max_length=25, description="Price item description")
    final_url: str = Field(..., min_length=1, description="Landing page URL")
    price_micros: int = Field(..., gt=0, description="Price in micros")
    currency_code: str = Field(default="BRL", min_length=3, max_length=3, description="Currency code")
    unit: str | None = Field(default=None, description="PER_HOUR, PER_DAY, PER_WEEK, PER_MONTH, PER_YEAR, PER_NIGHT")

    @field_validator("final_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"final_url must start with http:// or https://, got '{v}'")
        return v
