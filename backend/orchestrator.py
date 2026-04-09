from fastapi import FastAPI
from pydantic import BaseModel
import requests, json, os
from typing import Dict, Any, Callable
from backend.tools import image_gen
from backend.tools import doc_analyze
app = FastAPI()

LLM_URL = "http://127.0.0.1:8080/completion"

class UserRequest(BaseModel):
    goal: str
    files: dict | None = None

def call_llm(prompt: str, n_predict: int = 512) -> str:
    r = requests.post(LLM_URL, json={
        "prompt": prompt,
        "n_predict": n_predict
    })
    return r.json()["content"]

# ---------------- Reality Core ----------------

def reality_core(goal: str, context: dict | None = None) -> str:
    prompt = f"""
You are the Reality Core. Interpret this situation using real-world nuance, human behavior, exceptions, and context.

Goal:
{goal}

Context:
{json.dumps(context or {})[:2000]}

Output a detailed analysis in plain text.
"""
    return call_llm(prompt, n_predict=768)

# ---------------- Logic Core ----------------

def logic_core(goal: str, reality_analysis: str) -> str:
    prompt = f"""
You are the Logic Core. Analyze this situation using strict logic, consistency, and formal reasoning.

Goal:
{goal}

Reality analysis:
{reality_analysis}

Identify contradictions, inconsistencies, and rule violations. Output a detailed logical analysis.
"""
    return call_llm(prompt, n_predict=768)

# ------------------ Intent Classifier ------------------

def classify_intent(goal: str) -> str:
    """
    LLM-based intent classifier.
    Returns a short label like:
    image_generation, 3d_model, audio_generation, renpy_project,
    outline_writing, report_writing, legal_drafting, medical_explanation,
    document_writing, document_analysis, general_reasoning, etc.
    """
    prompt = f"""
You are an intent classifier for an AI orchestrator.

User request:
{goal!r}

Decide the SINGLE best high-level intent label for this request.
Choose ONLY ONE from (but you may also invent a close variant if needed):

image_generation, image_editing,
video_generation, video_editing,
audio_generation, music_generation, voice_generation, sound_effects,
2d_model, 3d_model, animation,
character_design, scene_design, environment_design,
renpy_project, renpy_script, renpy_assets, renpy_characters, renpy_scenes, renpy_logic,
outline_writing, syllabus_design, report_writing,
legal_drafting, medical_explanation,
document_writing, document_analysis, file_processing,
image_analysis, video_analysis, audio_analysis,
script_writing, story_writing, dialogue_writing,
worldbuilding, lore_generation,
code_generation, planning,
summarization, translation, classification, transcription,
general_reasoning

Respond with ONLY the label, no explanation.
"""
    raw = call_llm(prompt, n_predict=64)
    intent = raw.strip().split()[0].strip().lower()
    return intent


# ------------------ Rule-Based Intent Engine ------------------

def rule_intent(goal: str, has_uploads: bool) -> str:
    """
    Fast, deterministic rule-based intent guess.
    Returns a label or 'unknown' if rules can't confidently decide.
    """
    g = goal.lower()

    # Obvious image / visual
    img_keywords = ["image", "picture", "photo", "art", "logo",
                    "icon", "wallpaper", "render", "portrait"]
    if any(k in g for k in img_keywords):
        return "image_generation"

    # Obvious 2D / 3D model
    if "3d" in g or "2d" in g or "model" in g:
        return "3d_model" if "3d" in g else "2d_model"

    # Obvious audio / music / voice
    if any(k in g for k in ["audio", "music", "song", "voice", "instrument", "sound"]):
        return "audio_generation"

    # Obvious video
    if any(k in g for k in ["video", "clip", "footage", "render video"]):
        return "video_generation"

    # Obvious Ren'Py / VN
    if any(k in g for k in ["renpy", "ren'py", "visual novel", "vn route", "vn script"]):
        return "renpy_project"

    # Obvious outline / syllabus / report / legal / medical
    if "outline" in g:
        return "outline_writing"
    if "syllabus" in g or "course" in g:
        return "syllabus_design"
    if "report" in g or "analysis" in g or "brief" in g:
        return "report_writing"
    if any(k in g for k in ["motion", "pleading", "complaint", "contract", "legal"]):
        return "legal_drafting"
    if any(k in g for k in ["diagnosis", "interpretation", "lab result", "medical"]):
        return "medical_explanation"

    # Obvious document / file analysis
    if has_uploads:
        if any(k in g for k in ["analyze", "summarize", "extract", "review"]):
            return "document_analysis"

    # If nothing obvious matched
    return "unknown"


# ------------------ Intent Integrator ------------------

def integrate_intents(rule_label: str, llm_label: str) -> str:
    """
    Hybrid merge of rule-based and LLM-based intents.

    Priority:
    - If rule_label is specific and not 'unknown', prefer it for obvious cases.
    - If rule_label is 'unknown', fall back to llm_label.
    - If both disagree but both are specific, prefer the more actionable one.
    - If both are weak/unknown, fall back to general_reasoning.
    """
    rule_label = (rule_label or "").strip().lower()
    llm_label = (llm_label or "").strip().lower()

    # If rules know what to do and it's not generic, trust rules
    if rule_label and rule_label != "unknown":
        # If LLM agrees, great
        if llm_label == rule_label or not llm_label:
            return rule_label
        # If they disagree, prefer the more specific one (non-general_reasoning)
        if llm_label == "general_reasoning":
            return rule_label
        if rule_label == "general_reasoning":
            return llm_label
        # Both are specific but different: prefer LLM for flexibility
        return llm_label

    # Rules don't know → fall back to LLM
    if llm_label and llm_label != "unknown":
        return llm_label

    # Both are unknown/weak → default
    return "general_reasoning"


# ------------------ Hybrid Planner ------------------

def make_plan(goal: str) -> Dict[str, Any]:
    """
    Hybrid planner:
    - Rule engine proposes an intent (fast, deterministic).
    - LLM classifier proposes an intent (flexible, intelligent).
    - Integrator merges both into a final intent.
    - Planner builds tasks based on that final intent.
    """
    os.makedirs("workspace", exist_ok=True)
    uploads_meta = "workspace/last_uploads.json"
    has_uploads = os.path.exists(uploads_meta)

    # Step 1: rule-based guess
    rule_label = rule_intent(goal, has_uploads)

    # Step 2: LLM-based guess
    llm_label = classify_intent(goal)

    # Step 3: integrate both
    intent = integrate_intents(rule_label, llm_label)

    tasks: list[dict] = []

    # ---- Image / visual creation ----
    if intent in {
        "image_generation", "image_editing",
        "character_design", "scene_design",
        "environment_design", "animation"
    }:
        tasks.append({
            "id": "image_task",
            "tool": "image_gen",
            "params": {
                "prompt": goal
            }
        })

    # ---- 2D / 3D models ----
    elif intent in {"2d_model", "3d_model"}:
        tasks.append({
            "id": "model_task",
            "tool": "image_gen",  # swap to dedicated model tool later if you want
            "params": {
                "prompt": goal
            }
        })

    # ---- Audio / music / voice ----
    elif intent in {
        "audio_generation", "music_generation",
        "voice_generation", "sound_effects"
    }:
        tasks.append({
            "id": "audio_task",
            "tool": "text",  # placeholder until you wire an audio tool
            "params": {
                "prompt": f"Design or describe the requested audio:\n{goal!r}"
            }
        })

    # ---- Ren'Py / VN ----
    elif intent in {
        "renpy_project", "renpy_script", "renpy_assets",
        "renpy_characters", "renpy_scenes", "renpy_logic"
    }:
        tasks.append({
            "id": "renpy_task",
            "tool": "text",
            "params": {
                "prompt": (
                    "You are an expert in Ren'Py and visual novels. "
                    "Generate whatever the user is asking for (scripts, assets descriptions, logic, etc.):\n"
                    f"{goal!r}"
                )
            }
        })

    # ---- Document / writing / legal / medical / reports / outlines / syllabus ----
    elif intent in {
        "outline_writing", "syllabus_design", "report_writing",
        "legal_drafting", "medical_explanation",
        "document_writing", "script_writing", "story_writing",
        "dialogue_writing", "worldbuilding", "lore_generation"
    }:
        tasks.append({
            "id": "write_task",
            "tool": "text",
            "params": {
                "prompt": (
                    "Write or draft the requested content in a clear, structured way:\n"
                    f"{goal!r}"
                )
            }
        })

    # ---- Analysis / processing ----
    elif intent in {
        "document_analysis", "file_processing",
        "image_analysis", "video_analysis", "audio_analysis"
    }:
        tool_name = "doc_analyze" if has_uploads else "text"
        tasks.append({
            "id": "analyze_task",
            "tool": tool_name,
            "params": {
                "prompt": (
                    "Analyze the available files and respond to the user's request:\n"
                    f"{goal!r}"
                )
            }
        })

    # ---- Utility / general reasoning ----
    else:
        tasks.append({
            "id": "reason",
            "tool": "text",
            "params": {
                "prompt": (
                    "You are BigBrain-AI. Think step by step and respond to the user goal:\n"
                    f"{goal!r}"
                )
            }
        })

    plan = {
        "goal": goal,
        "intent": intent,
        "rule_intent": rule_label,
        "llm_intent": llm_label,
        "tasks": tasks
    }

    with open("workspace/last_plan.json", "w") as f:
        json.dump(plan, f, indent=2)

    return plan

# ---------------- Integrator ----------------

def integrator(goal: str, reality_analysis: str, logic_analysis: str) -> dict:
    prompt = f"""
You are the Integrator. Combine the Reality Core and Logic Core analyses.

Goal:
{goal}

Reality analysis:
{reality_analysis}

Logic analysis:
{logic_analysis}

If they contradict, generate questions to resolve the contradiction.
Then produce a final balanced conclusion.

Output JSON with:
- final_conclusion
- questions
- assumptions
- risks
- logic_score
- reality_score
"""
    raw = call_llm(prompt, n_predict=768)
    return json.loads(raw)

# ---------------- Tool Registry ----------------

ToolFunc = Callable[[dict, dict], Dict[str, Any]]
TOOLS: Dict[str, ToolFunc] = {}

def tool(name: str):
    def decorator(fn: ToolFunc):
        TOOLS[name] = fn
        return fn
    return decorator

@tool("text")
def tool_text(task: dict, context: dict) -> dict:
    text = call_llm(
        f"Task: {task['description']}\nUse context if helpful:\n{json.dumps(context)[:2000]}"
    )
    return {"status": "ok", "output": text}

@tool("image_gen")
def tool_image_gen(task: dict, context: dict):
    return image_gen.run(task, context)
    if has_uploads and any(k in g for k in ["pdf", "document", "file", "analyze", "summarize"]):
        return image_gen.run(task, context)

@tool("doc_analyze")
def tool_doc_analyze(task: dict, context: dict) -> dict:
    return doc_analyze.run(task, context)


# ---------------- API Endpoints ----------------

@app.post("/brain")
def brain(req: UserRequest):
    reality = reality_core(req.goal, req.files or {})
    logic = logic_core(req.goal, reality)
    integrated = integrator(req.goal, reality, logic)
    return {
        "reality": reality,
        "logic": logic,
        "integrated": integrated
    }

@app.post("/plan")
def plan(req: UserRequest):
    plan = make_plan(req.goal)
    os.makedirs("workspace", exist_ok=True)
    with open("workspace/last_plan.json", "w") as f:
        json.dump(plan, f, indent=2)
    return plan

@app.post("/execute")
def execute(req: UserRequest):
    plan = make_plan(req.goal)
    results: Dict[str, Any] = {}
    for task in plan["tasks"]:
        deps = task.get("depends_on", [])
        if not all(d in results and results[d].get("status") == "ok" for d in deps):
            results[task["id"]] = {"status": "skipped_deps"}
            continue
        res = execute_task(task, results)
        results[task["id"]] = res
    with open("workspace/last_results.json", "w") as f:
        json.dump(results, f, indent=2)
    return {"plan": plan, "results": results}

