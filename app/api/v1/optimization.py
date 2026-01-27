from fastapi import APIRouter, HTTPException

from app.schemas.optimization import OptimizationRequest, OptimizationResponse
from app.services.optimization_service import optimization_service

router = APIRouter()


@router.post("/optimize", response_model=OptimizationResponse, summary="Optimize user input")
async def optimize_query(request: OptimizationRequest):
    """
    接收用户输入，使用轻量级 LLM (Qwen-Turbo) 进行优化，使其更加清晰明确。
    """
    if not request.input.strip():
        raise HTTPException(status_code=400, detail="Input cannot be empty")

    optimized = await optimization_service.optimize_input(request.input)
    return OptimizationResponse(optimized_input=optimized)
