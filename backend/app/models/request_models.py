from pydantic import BaseModel
from typing import List

class CitizenBiasRequest(BaseModel):
    domain: str
    sex: str
    race: str
    age_group: str

class OrganizationDecision(BaseModel):
    sex: str
    race: str
    age_group: str
    outcome: int

class OrganizationAuditRequest(BaseModel):
    domain: str
    decisions: List[OrganizationDecision]
