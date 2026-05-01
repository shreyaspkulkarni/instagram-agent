from pydantic import BaseModel, Field


class CaptionDraft(BaseModel):
    caption: str = Field(
        description="The Instagram caption. Conversational, authentic, matches the photo's mood."
    )
    hashtags: list[str] = Field(
        description="8-15 relevant hashtags without the # symbol. Mix of niche, medium, and broad tags."
    )
    style_notes: str = Field(
        description="One sentence explaining the style choice — e.g. 'minimal storytelling with a question to drive comments'"
    )
