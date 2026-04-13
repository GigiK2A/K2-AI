import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DONE = "done"


class AgentName(str, Enum):
    ORCHESTRATOR = "orchestrator"
    CHIEF_OF_STAFF = "chief_of_staff"
    OFFER_POSITIONING = "offer_positioning"
    MARKET_INTELLIGENCE = "market_intelligence"
    BRAND_STRATEGY = "brand_strategy"
    MARKETING_STRATEGY = "marketing_strategy"
    CONTENT_ENGINE = "content_engine"
    LEAD_GENERATION = "lead_generation"
    OUTREACH = "outreach"
    SALES_ENABLEMENT = "sales_enablement"
    SOLUTION_ARCHITECT = "solution_architect"
    PROJECT_OPERATIONS = "project_operations"
    KNOWLEDGE = "knowledge"
    FINANCE_KPI = "finance_kpi"
    RISK_REVIEW = "risk_review"
    LEGAL = "legal"
    GEO_SEO = "geo_seo"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    assigned_to: AgentName
    requested_by: str = "founder"
    status: TaskStatus = TaskStatus.PENDING
    priority: int = Field(default=3, ge=1, le=5)
    input_data: Optional[dict[str, Any]] = None
    output_data: Optional[dict[str, Any]] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent: AgentName
    task_id: Optional[str] = None
    action: str
    llm_provider: Optional[LLMProvider] = None
    llm_model: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    status: str
    tokens_used: Optional[int] = None
    duration_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Approval(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    agent: AgentName
    content_type: str
    content_preview: str
    full_content: dict[str, Any]
    status: TaskStatus = TaskStatus.DRAFT
    founder_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None


class PipelineLead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    company: Optional[str] = None
    sector: Optional[str] = None
    channel: Optional[str] = None
    pain_point: Optional[str] = None
    offer_fit: Optional[str] = None
    status: str = "identified"
    score: Optional[int] = Field(default=None, ge=1, le=10)
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SharedMemory(BaseModel):
    key: str
    value: Any
    category: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str = "founder"
