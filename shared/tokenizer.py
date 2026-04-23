"""Wixie shared tokenizer — heuristic token estimation. Stdlib only."""
import re


def estimate_tokens(text):
    """Estimate token count using word count + markup overhead heuristic.

    Approximation: ~1.3 tokens per word, plus 2 tokens per markup element
    (code fences, XML tags). Accurate within ~15% for English text.
    """
    words = len(text.split())
    code_blocks = len(re.findall(r'```', text))
    xml_tags = len(re.findall(r'<\w+', text))
    markup_bonus = (code_blocks + xml_tags) * 2
    return int(words * 1.3 + markup_bonus)


def detect_model(text):
    """Detect target model from prompt content. Returns model ID or None."""
    tl = text.lower()
    if re.search(r'\b(claude|anthropic)\b|<(instructions|context|example)>', tl):
        return "claude-sonnet-4-6"
    if re.search(r'\b(gpt-4\.1|gpt-4o)\b', tl):
        return "gpt-4o"
    if re.search(r'\b(gpt-5)\b', tl):
        return "gpt-5"
    if re.search(r'\b(o1|o3|o4-mini)\b', tl):
        return "o3"
    if re.search(r'\b(gemini)\b', tl):
        return "gemini-2.5-pro"
    if re.search(r'\b(llama)\b', tl):
        return "llama-4"
    if re.search(r'\b(mistral|mixtral)\b', tl):
        return "mistral-large"
    return None
