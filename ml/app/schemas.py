from typing import Literal
from pydantic import BaseModel, Field, model_validator
from .data import FEATURES
class PredictionRequest(BaseModel):
    task: Literal["mortality","long_stay","readmission"]
    sample_id: int | None = Field(default=None,ge=0,le=11)
    features: dict[str,float|None] | None = None
    @model_validator(mode="after")
    def source(self):
        if self.sample_id is None and not self.features: raise ValueError("provide sample_id or features")
        if self.features:
            unknown=set(self.features)-set(FEATURES)
            if unknown: raise ValueError(f"unknown features: {sorted(unknown)}")
        return self
