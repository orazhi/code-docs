from fastapi import FastAPI, HTTPException
from app.schemas import TranslationRequest, TranslationResponse, QCRequest, QCResponse
from app.services import perform_translation, perform_qc
from app.config import settings

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.VERSION,
    description="Microservice for Agentic Translation Pipeline"
)

@app.post("/AI_Translation", response_model=TranslationResponse)
async def ai_translation(request: TranslationRequest):
    try:
        result = await perform_translation(
            request.text, 
            request.target_language, 
            request.extra_prompt or ""
        )

        return {"translated_text": result}
    except Exception as e:
        # Log the error in a real app
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@app.post("/AI_QC", response_model=QCResponse)
async def ai_qc(request: QCRequest):
    try:
        result = await perform_qc(request.source_text, request.translated_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QC Validation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
