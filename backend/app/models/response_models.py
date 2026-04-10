from pydantic import BaseModel
from typing import List, Optional

class BiasData(BaseModel):
    approval_rate: float
    disparity_ratio: float
    fourfifths_breach: bool
    sample_size: int

class CitizenBiasResponse(BaseModel):
    status: str
    data: Optional[BiasData] = None
    explanation: Optional[str] = None
    message: Optional[str] = None

class BiasSummary(BaseModel):
    total_records: int
    flagged_count: int

class FlaggedSlice(BaseModel):
    sex: Optional[str] = None
    race: Optional[str] = None
    age_group: Optional[str] = None
    gender: Optional[str] = None
    education: Optional[str] = None
    income_group: Optional[str] = None
    disparity_ratio: float
    priority: str
    approval_rate: Optional[float] = None
    reference_approval_rate: Optional[float] = None
    sample_size: Optional[int] = None
    remediation_note: Optional[str] = None

class RemediationPriority(BaseModel):
    slice: str
    priority: str
    recommendation: str

class OrganizationAuditResponse(BaseModel):
    bias_summary: BiasSummary
    flagged_slices: List[FlaggedSlice]
    remediation_priorities: List[RemediationPriority]
    gemini_report: Optional[str] = None
