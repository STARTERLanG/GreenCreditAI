from pydantic import BaseModel, Field


class OptimizationRequest(BaseModel):
    input: str = Field(..., description="The user input to optimize", min_length=1)


class OptimizationResponse(BaseModel):
    optimized_input: str = Field(..., description="The optimized version of the input")
