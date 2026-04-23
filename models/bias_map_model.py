from pydantic import BaseModel, Field

class BiasContribution(BaseModel):
    city: str = Field(..., min_length=2)
    sector: str = Field(..., pattern="^(hiring|lending)$")
    disparity_ratio: float = Field(..., gt=0)
    consent: bool