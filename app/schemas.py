from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class HumorMechanism(str, Enum):
    MISDIRECTION = "misdirection"
    REVERSAL = "reversal"
    SPECIFICITY = "specificity"
    EXAGGERATION = "exaggeration"
    UNDERSTATEMENT = "understatement"
    WORDPLAY = "wordplay"
    CALLBACK = "callback"
    RULE_OF_THREE = "rule_of_three"
    INCONGRUITY = "incongruity"
    IRONY = "irony"
    ABSURDITY = "absurdity"
    ANALOGY = "analogy"
    SATIRE = "satire"
    SELF_DEPRECATION = "self_deprecation"
    OBSERVATIONAL = "observational"
    OTHER = "other"


class ComedyGene(str, Enum):
    BREVITY = "brevity"
    SPECIFICITY = "specificity"
    MISDIRECTION = "misdirection"
    PUNCHLINE = "punchline"
    CALLBACK = "callback"
    TIMING = "timing"
    TONE = "tone"
    CULTURAL_ACCESSIBILITY = "cultural_accessibility"


class AudienceContext(BaseModel):
    target_audience: str = Field(default="general adult audience", min_length=2, max_length=200)
    format: str = Field(default="short written joke", min_length=2, max_length=100)
    desired_tone: str = Field(default="playful", min_length=2, max_length=100)
    language: str = Field(default="English", min_length=2, max_length=50)
    constraints: list[str] = Field(default_factory=list, max_length=10)


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=3, max_length=4000)
    context: AudienceContext = Field(default_factory=AudienceContext)


class MechanismEvidence(BaseModel):
    mechanism: HumorMechanism
    evidence: str = Field(min_length=1, max_length=500)
    role: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)


class HumorGenome(BaseModel):
    input_text: str = Field(min_length=3, max_length=4000)
    language: str = Field(min_length=2, max_length=50)
    premise: str = Field(min_length=1, max_length=1000)
    setup: str = Field(min_length=1, max_length=1500)
    assumptions: list[str] = Field(default_factory=list, max_length=5)
    turn: str = Field(min_length=1, max_length=1000)
    punchline: str = Field(min_length=1, max_length=1000)
    mechanisms: list[MechanismEvidence] = Field(min_length=1, max_length=5)
    timing_notes: list[str] = Field(default_factory=list, max_length=4)
    cultural_dependencies: list[str] = Field(default_factory=list, max_length=4)
    risks: list[str] = Field(default_factory=list, max_length=4)
    confidence: float = Field(ge=0, le=1)
    alternative_readings: list[str] = Field(default_factory=list, max_length=3)


class MutationRequest(BaseModel):
    source_text: str = Field(min_length=3, max_length=4000)
    genome: HumorGenome
    target_gene: ComedyGene
    context: AudienceContext = Field(default_factory=AudienceContext)
    invariants: list[str] = Field(
        default_factory=lambda: ["preserve the premise", "preserve the author's voice"],
        min_length=1,
        max_length=10,
    )
    number_of_variants: int = Field(default=2, ge=2, le=3)


class MutationVariant(BaseModel):
    label: str = Field(min_length=1, max_length=20)
    text: str = Field(min_length=3, max_length=4000)
    changed_gene: ComedyGene
    change_summary: str = Field(min_length=1, max_length=500)
    preserved_invariants: list[str] = Field(min_length=1, max_length=10)
    changed_only_target_gene: bool
    confidence: float = Field(ge=0, le=1)


class MutationResponse(BaseModel):
    source_text: str = Field(min_length=3, max_length=4000)
    target_gene: ComedyGene
    variants: list[MutationVariant] = Field(min_length=2, max_length=3)
    caveats: list[str] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def variants_match_target(self) -> "MutationResponse":
        if any(variant.changed_gene != self.target_gene for variant in self.variants):
            raise ValueError("Every variant must change the requested target_gene")
        if any(not variant.changed_only_target_gene for variant in self.variants):
            raise ValueError("Every variant must pass the one-gene self-check")
        return self


class CompareRequest(BaseModel):
    source_text: str = Field(min_length=3, max_length=4000)
    variants: list[MutationVariant] = Field(min_length=2, max_length=3)
    context: AudienceContext = Field(default_factory=AudienceContext)


class VariantObservation(BaseModel):
    label: str = Field(min_length=1, max_length=20)
    mechanism_effect: str = Field(min_length=1, max_length=600)
    likely_strengths: list[str] = Field(default_factory=list, max_length=4)
    likely_weaknesses: list[str] = Field(default_factory=list, max_length=4)
    uncertainty: str = Field(min_length=1, max_length=500)


class ComparisonResponse(BaseModel):
    observations: list[VariantObservation] = Field(min_length=2, max_length=3)
    key_tradeoff: str = Field(min_length=1, max_length=800)
    suggested_human_test: str = Field(min_length=1, max_length=500)
    limitations: list[str] = Field(min_length=1, max_length=5)


class FlowRequest(BaseModel):
    text: str = Field(min_length=3, max_length=4000)
    target_gene: ComedyGene
    context: AudienceContext = Field(default_factory=AudienceContext)
    number_of_variants: int = Field(default=2, ge=2, le=3)


class FlowResponse(BaseModel):
    genome: HumorGenome
    mutation: MutationResponse
    comparison: ComparisonResponse
    model: str
    stage_latency_seconds: dict[str, float]
