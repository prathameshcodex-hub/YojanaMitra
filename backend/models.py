from pydantic import BaseModel
from typing import Optional


class UserProfile(BaseModel):
    age: int
    state: str
    district: str
    gender: str

    occupation: str
    annual_income: float

    category: str

    land_owned: bool
    land_area_acres: Optional[float] = None

    family_size: int
    education: str

    disability_status: bool

    marital_status: str
    residence: str

    # Additional eligibility/exclusion information
    income_tax_payer: bool
    government_employee: bool
    government_pensioner: bool
    monthly_pension: Optional[float] = None
    professional_practice: bool
    institutional_landholder: bool