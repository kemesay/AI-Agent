"""Raw document extraction endpoints (Agents 1-3), independent of risk scoring."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from google import genai

from trade_service_agents.core.logging import get_logger
from trade_service_agents.extraction.prompts import base_extraction_prompt, proforma_extraction_prompt
from trade_service_agents.extraction.vision import get_client, run_extraction

LOGGER = get_logger(__name__)

router = APIRouter()


@router.post("/extract")
async def extract(file: UploadFile = File(...), client: genai.Client = Depends(get_client)):
    try:
        return run_extraction(file, base_extraction_prompt, client)
    except HTTPException as exc:
        raise exc
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Unexpected error during /extract")
        return JSONResponse(status_code=500, content={"error": str(exc)})


@router.post("/extract_proforma")
async def extract_proforma(file: UploadFile = File(...), client: genai.Client = Depends(get_client)):
    try:
        return run_extraction(file, proforma_extraction_prompt, client)
    except HTTPException as exc:
        raise exc
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Unexpected error during /extract_proforma")
        return JSONResponse(status_code=500, content={"error": str(exc)})
