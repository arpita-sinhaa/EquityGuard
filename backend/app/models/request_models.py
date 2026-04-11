from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator
from typing import List
from typing import Optional

class CitizenBiasRequest(BaseModel):
    domain: str
    sex: Optional[str] = None
    race: Optional[str] = None
    age_group: Optional[str] = None
    gender: Optional[str] = None
    education: Optional[str] = None
    income_group: Optional[str] = Field(
        default=None,
        description="Lending only: low (<= INR 3,000), mid (INR 3,001-6,000), high (INR 6,001-10,000), very_high (> INR 10,000)",
    )
    country: Optional[str] = None

    @model_validator(mode="after")
    def validate_domain_fields(self):
        domain = self.domain.lower()

        if domain == "lending":
            required = {
                "gender": self.gender,
                "education": self.education,
                "income_group": self.income_group,
            }
        else:
            required = {
                "sex": self.sex,
                "race": self.race,
                "age_group": self.age_group,
            }

        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing required fields for {domain}: {', '.join(missing)}")

        return self

class OrganizationDecision(BaseModel):
    sex: Optional[str] = None
    race: Optional[str] = None
    age_group: Optional[str] = None
    gender: Optional[str] = None
    education: Optional[str] = None
    income_group: Optional[str] = None
    outcome: int = Field(..., ge=0, le=1)

class OrganizationAuditRequest(BaseModel):
    domain: str
    decisions: List[OrganizationDecision] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_domain_decisions(self):
        domain = self.domain.lower()

        for idx, decision in enumerate(self.decisions):
            if domain == "lending":
                required = {
                    "gender": decision.gender,
                    "education": decision.education,
                    "income_group": decision.income_group,
                }
            else:
                required = {
                    "sex": decision.sex,
                    "race": decision.race,
                    "age_group": decision.age_group,
                }

            missing = [key for key, value in required.items() if not value]
            if missing:
                raise ValueError(
                    f"Decision index {idx} missing required fields for {domain}: {', '.join(missing)}"
                )

        return self
