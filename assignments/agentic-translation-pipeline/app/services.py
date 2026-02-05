import ast
import json
import re
# from ollama import AsyncClient
from huggingface_hub import AsyncInferenceClient
from app.config import settings
from app.prompts import get_translation_system_prompt, get_qc_system_prompt

# client = AsyncClient(host=settings.OLLAMA_HOST)
client = AsyncInferenceClient(token=settings.HF_TOKEN)

async def perform_translation(text: str, target_lang: str, extra_prompt: str) -> str:
    """
    Calls LLM to translate text.
    """
    system_prompt = get_translation_system_prompt(target_lang, extra_prompt)

    # response = await client.chat(
    #     model=settings.TRANSLATION_MODEL,
    #     messages=[
    #         {'role': 'system', 'content': system_prompt},
    #         {'role': 'user', 'content': text}
    #     ],
    #     options={'temperature': 0.3},
    # )

    response = await client.chat_completion(
        model=settings.TRANSLATION_MODEL,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': text}
        ],
        temperature=0.3,
        max_tokens=1024,
    )

    # return response['message']['content'].strip()
    content =  response.choices[0].message.content.strip()
    if content:
        content = content.split("</think>")[-1].strip()
    return content

async def perform_qc(source: str, translation: str) -> dict:
    """
    Calls Ollama to QC the translation and returns structured data.
    """
    system_prompt = get_qc_system_prompt()
    user_content = f'''Source Text:\n"""\n{source}"""\n\nTarget Translation:\n"""{translation}\n"""'''

    # response = await client.chat(
    #     model=settings.QC_MODEL,
    #     messages=[
    #         {'role': 'system', 'content': system_prompt},
    #         {'role': 'user', 'content': user_content}
    #     ],
    #     format='json',
    #     options={'temperature': 0.1},
    # )
    #
    # content = response['message']['content']

    response = await client.chat_completion(
        model=settings.QC_MODEL,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_content}
        ],
        temperature=0.1,
        max_tokens=500
    )
    content = response.choices[0].message.content

    # 1. Strip Markdown Code Blocks (common issue)
    clean_content = re.sub(r"```json\s*", "", content, flags=re.IGNORECASE)
    clean_content = re.sub(r"```\s*", "", clean_content).strip()

    # 2. Extract the JSON object using Regex (in case of chatty intro/outro)
    # This finds the first opening brace and the last closing brace
    match = re.search(r'\{.*\}', clean_content, re.DOTALL)
    if match:
        clean_content = match.group()

    try:
        # Attempt 1: Standard JSON parse
        data = json.loads(clean_content)
    except json.JSONDecodeError:
        try:
            # Attempt 2: Python Literal Evaluation
            # Small models often output {'key': 'value'} (single quotes).
            # This is valid Python dict but invalid JSON. ast.literal_eval handles this safely.
            data = ast.literal_eval(clean_content)
        except (ValueError, SyntaxError):
            # Attempt 3: Last Resort - Fix specific syntax issues manually
            # Sometimes models leave trailing commas: {"a": 1,}
            try:
                # Remove trailing commas before closing braces/brackets
                fixed_content = re.sub(r',\s*([\]}])', r'\1', clean_content)
                data = json.loads(fixed_content)
            except:
                print(f"FAILED PARSING CONTENT: {clean_content}")  # Log for debugging
                # Fallback default to prevent app crash
                data = {"accuracy_score": 1, "hallucination_score": 1, "reasoning": "JSON Parsing Failed"}

    # Business Logic for is_pass (Deterministic is safer than LLM generation)
    # The assignment says: True if scores >= 8 (example)
    acc = data.get('accuracy_score', 1)
    hal = data.get('hallucination_score', 1)
    if hal <= 1:
        hal = 1
    if acc <= 1:
        acc = 1
    if acc >= 9:
        hal = 10

    is_pass = (acc >= settings.PASS_THRESHOLD) and (hal >= settings.PASS_THRESHOLD)

    return {
        "accuracy_score": acc,
        "hallucination_score": hal,
        "reasoning": data.get('reasoning', "No reasoning provided"),
        "is_pass": is_pass
    }
