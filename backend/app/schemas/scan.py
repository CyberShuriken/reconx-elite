from typing import Literal

from pydantic import BaseModel, Field

TemplateCategory = Literal["cves", "exposures", "misconfiguration", "fuzzing"]
SeverityLevel = Literal["low", "medium", "high", "critical"]


class ScanConfigRequest(BaseModel):
    selected_templates: list[TemplateCategory] = Field(default_factory=list)
    severity_filter: list[SeverityLevel] = Field(default_factory=list)
