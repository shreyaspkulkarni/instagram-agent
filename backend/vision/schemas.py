from pydantic import BaseModel, Field


class EditParams(BaseModel):
    """Machine-readable edit parameters — directly consumable by Pillow."""
    rotation: int = Field(
        default=0,
        description="Degrees to rotate clockwise: 0, 90, 180, or 270"
    )
    brightness: float = Field(
        default=0,
        ge=-100, le=100,
        description="Brightness adjustment: -100 (very dark) to +100 (very bright), 0 = no change"
    )
    contrast: float = Field(
        default=0,
        ge=-100, le=100,
        description="Contrast adjustment: -100 to +100, 0 = no change"
    )
    saturation: float = Field(
        default=0,
        ge=-100, le=100,
        description="Color saturation: -100 (grayscale) to +100 (very vivid), 0 = no change"
    )
    sharpness: float = Field(
        default=0,
        ge=0, le=100,
        description="Sharpness boost: 0 = no change, 100 = maximum sharpening"
    )
    crop_ratio: str = Field(
        default="original",
        description="Target crop ratio: original, 1:1, 4:5, or 16:9"
    )


class PhotoScore(BaseModel):
    score: float = Field(
        ge=0, le=10,
        description="Overall Instagram worthiness score from 0 to 10",
    )
    composition_notes: str = Field(
        description="Notes on framing, rule of thirds, leading lines, symmetry"
    )
    lighting_notes: str = Field(
        description="Notes on exposure, shadows, highlights, golden hour, harsh light"
    )
    subject_notes: str = Field(
        description="Notes on subject clarity, focus, background separation"
    )
    niche_fit: str = Field(
        description="How well this fits a travel/lifestyle/photography Instagram niche"
    )
    edit_suggestions: list[str] = Field(
        description="Human-readable edit suggestions explaining what to fix and why"
    )
    edit_params: EditParams = Field(
        description="Numeric edit parameters to apply with Pillow — brightness, contrast, saturation, sharpness, rotation, crop"
    )
    recommended_format: str = Field(
        description="Best Instagram crop: square_1_1, portrait_4_5, or landscape_16_9"
    )
    post_worthy: bool = Field(
        description="True if worth posting as-is or with the suggested edits applied"
    )
