import json
import httpx
import asyncio
import logging
from datetime import datetime
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
import os

MEMORY_FILE = "learned_corrections.json"

def load_long_term_memory():
    """Load correction history from disk."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_to_long_term_memory(source: str, correction: str):
    """Append a new correction to disk."""
    history = load_long_term_memory()
    # Avoid duplicates
    if not any(h['source'] == source for h in history):
        history.append({"source": source, "correction": correction})
        with open(MEMORY_FILE, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

# --- 1. Structured Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("TranslationAgent")


def log_step(node_name: str, state_update: dict, message: str = ""):
    """Helper to log agent actions in a structured format."""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "node": node_name,
        "message": message,
        "state_snapshot": state_update
    }
    logger.info(f"STEP_UPDATE: {json.dumps(log_data)}")


# --- 2. State & API Setup ---
class AgentState(TypedDict):
    source_text: str
    target_language: str
    translated_text: Optional[str]
    qc_results: Optional[dict]
    correction_history: List[dict]


BASE_URL = "http://localhost:8000"

timeout = httpx.Timeout(
    connect=10.0,
    read=180.0,
    write=30.0,
    pool=10.0
)

limits = httpx.Limits(
    max_connections=20,
    max_keepalive_connections=5
)

async def call_api(endpoint: str, payload: dict):
    async with httpx.AsyncClient(
        timeout=timeout,
        limits=limits
    ) as client:
        response = await client.post(f"{BASE_URL}{endpoint}", json=payload)
        response.raise_for_status()
        return response.json()


# --- 3. Nodes with Detailed Logging ---

async def translation_node(state: AgentState):
    if state["correction_history"]:
        few_shot = "\n".join([f"Src: {h['source']} | Fix: {h['correction']}" for h in state["correction_history"]])
    else:
        few_shot = None

    payload = {
        "text": state["source_text"],
        "target_language": state["target_language"],
        "extra_prompt": f"History:\n{few_shot}" if few_shot else ""
    }

    result = await call_api("/AI_Translation", payload)

    log_step("translate", {"translated_text": result["translated_text"]}, "API Call Successful")
    return {"translated_text": result["translated_text"]}


async def qc_node(state: AgentState):
    payload = {
        "source_text": state["source_text"],
        "translated_text": state["translated_text"]
    }

    result = await call_api("/AI_QC", payload)

    # testing
    if "FAILME" in state["source_text"]:
        logger.info("TESTING MODE: Forcing QC Failure to test HITL")
        result["is_pass"] = False
        result["reasoning"] = "Forced failure for testing purposes."

    log_step("qc", {"qc_results": result}, f"QC Pass: {result['is_pass']}")
    return {"qc_results": result}


async def human_review_node(state: AgentState):
    logger.warning(f"HITL: Interrupting for manual review. Reason: {state['qc_results'].get('reasoning')}")

    review_data = interrupt({
        "instruction": "Provide correction",
        "original": state["translated_text"]
    })

    corrected_text = review_data["corrected_text"]
    save_to_long_term_memory(state["source_text"], corrected_text)
    current_history = load_long_term_memory()

    log_step("human_review", {"correction_history_len": len(current_history)}, "Human provided correction")
    return {"translated_text": corrected_text, "correction_history": current_history}


async def save_result_node(state: AgentState):
    log_entry = {
        "final_translation": state["translated_text"],
        "qc_final": state["qc_results"],
        "shots_used": len(state["correction_history"])
    }
    # Persistence logging
    with open("audit_trail.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    log_step("save_result", {}, "Result persisted to audit_trail.jsonl")
    return state


# --- 4. Logic & Graph Construction ---

def route_after_qc(state: AgentState):
    return "save_result" if state["qc_results"].get("is_pass") else "human_review"


workflow = StateGraph(AgentState)
workflow.add_node("translate", translation_node)
workflow.add_node("qc", qc_node)
workflow.add_node("human_review", human_review_node)
workflow.add_node("save_result", save_result_node)

workflow.add_edge(START, "translate")
workflow.add_edge("translate", "qc")
workflow.add_conditional_edges("qc", route_after_qc)
workflow.add_edge("human_review", "save_result")
workflow.add_edge("save_result", END)

app = workflow.compile(checkpointer=MemorySaver())


# --- 5. Execution Logic ---
# --- 5. Execution Logic ---
async def run_workflow(source: str, lang: str):
    config = {"configurable": {"thread_id": "unique_session_012"}} # Changed ID to ensure fresh state

    initial_input = {
        "source_text": source,
        "target_language": lang,
        "correction_history": []
    }

    print(f"\n--- Starting Workflow for: {source} ---")

    # 1. Start execution
    async for event in app.astream(initial_input, config, stream_mode="updates"):
        for node_name, node_output in event.items():
            print(f"\n[Stream Log] Node '{node_name}' finished.")
            if node_name == "translate":
                print(f"   > Output: {node_output.get('translated_text')}")
            elif node_name == "qc":
                passed = node_output['qc_results'].get('is_pass')
                print(f"   > Output: QC {'Passed' if passed else 'Failed'}")

    # 2. Check the checkpoint
    state_snapshot = await app.aget_state(config)

    if state_snapshot.next:
        print("\n\n>>> 🛑 HITL TRIGGERED: Quality Control Failed.")
        print(f"Reason: {state_snapshot.values['qc_results'].get('reasoning')}")
        print(f"Bad Translation: {state_snapshot.values['translated_text']}")

        user_correction = input("\n✍️  Enter the corrected translation: ")

        print("\n--- Resuming Workflow with Human Input ---")
        # 3. Resume
        async for event in app.astream(
                Command(resume={"corrected_text": user_correction}),
                config,
                stream_mode="updates"
        ):
             for node_name, node_output in event.items():
                if node_name == "human_review":
                     print(f"[Stream Log] Human Review applied. New Translation: {node_output['translated_text']}")
                elif node_name == "save_result":
                     print("[Stream Log] Result saved to audit trail.")

    print("\n--- Workflow Complete ---")

if __name__ == "__main__":
    asyncio.run(run_workflow("Did you have your lunch Preetha!", "Hindi"))
