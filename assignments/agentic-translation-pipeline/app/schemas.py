from pydantic import BaseModel, Field
from typing import Optional

# --- Endpoint 1: Translation Schemas ---
class TranslationRequest(BaseModel):
    text: str = Field(..., description="The source text to translate (English)")
    target_language: str = Field(..., description="Target language name (e.g., 'French')")
    extra_prompt: Optional[str] = Field(None, description="Tone or style instructions (e.g., 'Use legal tone')")

class TranslationResponse(BaseModel):
    translated_text: str

# --- Endpoint 2: QC Schemas ---
class QCRequest(BaseModel):
    source_text: str
    translated_text: str

class QCResponse(BaseModel):
    accuracy_score: int = Field(..., ge=1, le=10)
    hallucination_score: int = Field(..., ge=1, le=10)
    reasoning: str
    is_pass: bool
