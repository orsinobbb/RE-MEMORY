from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field

class Kind(StrEnum):
    FACT="FACT"; CLAIM="CLAIM"; INFERENCE="INFERENCE"; GOAL="GOAL"
    CONSTRAINT="CONSTRAINT"; DECISION="DECISION"; ACTION="ACTION"; RESULT="RESULT"; UNKNOWN="UNKNOWN"

class Record(BaseModel):
    id: str
    user_id: str
    project_id: str = ""
    created_at: str = ""

class FactCell(Record):
    kind: Kind
    subject: str
    relation: str
    content: str
    evidence_ids: list[str] = Field(default_factory=list)
    valid_from: str
    valid_to: str | None = None
    version: int = 1
    verification: str = "UNVERIFIED"
    trust: str = "UNKNOWN"
    related_ids: list[str] = Field(default_factory=list)
    access: str = "OWNER"
    superseded: bool = False
    conflict: bool = False
    mandatory: bool = False

class Alias(Record):
    alias: str
    evidence_ids: list[str]
    uses: int = 1
    last_used: str
    method: str = "INFERENCE"
    status: str = "CANDIDATE"
    strength: float = 0.5
    ambiguous: bool = False

class User(Record):
    name: str
class Project(Record):
    name: str
    topic: str
    description: str
    last_active: str
class Evidence(Record):
    source: str
    content: str
    version: int = 1
    trusted: bool = False
class Task(Record):
    title: str
    status: str = "PENDING"
    dependency_ids: list[str] = Field(default_factory=list)
    required_artifact_ids: list[str] = Field(default_factory=list)
    artifact_id: str | None = None
    tool: str = "markdown_handoff"
class Artifact(Record):
    task_id: str
    content: str
    sha256: str
    verified: bool = False
    mode: str = "SIMULATION"
class Object(Record):
    payload: dict[str, Any] = Field(default_factory=dict)
class Topic(Object): pass
class Entity(Object): pass
class Event(Object): pass
class Goal(Object): pass
class Constraint(Object): pass
class Decision(Object): pass
class Relation(Object): pass
class MemorySnapshot(Object): pass
class RetrievalSession(Object): pass
class RetrievalTrace(Object): pass
class ModelCall(Object): pass
class EvaluationResult(Object): pass
