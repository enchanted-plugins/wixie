"""Flux shared constants — used by all scripts."""

AXES = ["Clarity", "Completeness", "Efficiency", "Model Fit", "Failure Resilience"]

FILLER_PHRASES = [
    r"it's worth noting", r"please note that", r"as an AI", r"I want you to",
    r"I need you to", r"please make sure", r"it is important to note",
    r"keep in mind", r"I would like you to", r"please ensure", r"in order to",
]

HEDGE_WORDS = [
    r"maybe", r"perhaps", r"possibly", r"try to",
    r"if possible", r"somewhat", r"might want to",
]

MODEL_PATTERNS = {
    "claude-sonnet-4-6": r'\b(claude|anthropic)\b|<(instructions|context|example)>',
    "gpt-4o": r'\b(gpt-4\.1|gpt-4o)\b',
    "gpt-5": r'\b(gpt-5)\b',
    "o3": r'\b(o1|o3|o4-mini|o-series)\b',
    "gemini-2.5-pro": r'\b(gemini|google ai)\b',
    "llama-4": r'\b(llama)\b',
    "mistral-large": r'\b(mistral|mixtral)\b',
}
