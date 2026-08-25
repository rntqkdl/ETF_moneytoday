"""
src/database/models.py
시스템 전반에서 사용하는 엔티티 및 DTO Pydantic 모델 정의
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ETFMasterRecord(BaseModel):
    ticker: str
    name: str
    issuer: str
    brand: str
    cluster_id: str
    cluster_name: str
    is_fx_hedged: bool = False
    is_synthetic: bool = False
    is_active: bool = False
    is_covered_call: bool = False
    is_pension_eligible: bool = True
    description: str
    key_themes: List[str] = Field(default_factory=list)
    expense_ratio: float = 0.0045
    aum_billion_krw: float = 150.0

class RAGSearchResult(BaseModel):
    score: float
    ticker: str
    name: str
    issuer: str
    brand: str
    cluster_id: str
    cluster_name: str
    is_fx_hedged: bool
    is_covered_call: bool
    snippet: str

class ClusterViewItem(BaseModel):
    cluster_id: str
    expected_return: float
    confidence: float
    top_pick: str

class QuantDecisionOutput(BaseModel):
    regime: str
    confidence_score: float
    cluster_views: List[ClusterViewItem]
    cash_park_ratio: float
    reasoning: str
