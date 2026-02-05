from json import load
from app.config import settings

with open(settings.LANG_CODES_PATH, 'r') as f:
    langCodes = load(f)

def get_qc_system_prompt() -> str:
    return f'''### ROLE
You are an expert Linguistic QA System. Your task is to evaluate a translation from English to [Target Language] based on two strict metrics.

### METRICS & SCORING RUBRIC (1-10)

1. Accuracy (Meaning & Intent)
   - Focus: Does the translation convey the exact same meaning and intent as the source?
   - Penalty: Penalize for missing sentences, wrong tone, or misinterpreted context.
   - 10: Perfect meaning preservation. No missing info.
   - 1: Completely unrelated or incorrect meaning.

2. Hallucination (Freedom from Fabrication)
   - Focus: Does the translation contain information NOT present in the source?
   - 10: Clean. No added facts or fabricated details. (This is the best score).
   - 1: Severe hallucination. Contains significant invented information.

### OUTPUT FORMAT
You must respond with valid JSON only. Do not add conversational text.

{{
    "reasoning": "Step-by-step analysis of accuracy and potential hallucinations...",
    "accuracy_score": int,
    "hallucination_score": int,
}}

### INPUT
'''

def get_translation_system_prompt(target_lang: str, extra_instructions: str = "") -> str:
    target_code = langCodes.get(target_lang, [''])[0]
    base = f'''You are a professional English (en) to {target_lang} ({target_code}) translator. Your goal is to accurately convey the meaning and nuances of the original English text while adhering to {target_lang} grammar, vocabulary, and cultural sensitivities.
Produce only the {target_lang} translation, without any additional explanations or commentary. Please translate the following English text into {target_lang}'''

    if extra_instructions:
        base += f" along with these Style Instructions: {extra_instructions}"
    base += ":\n\n"
    return base
