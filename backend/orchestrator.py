from fastapi import FastAPI
from pydantic import BaseModel
import requests, json, os
from typing import Dict, Any, Callable
from tools import image_gen
from tools import doc_analyze
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
def tool_image_gen(task: dict, context: dict) -> dict:
    return image_gen.run(task, context)

@tool("doc_analyze")
def tool_doc_analyze(task: dict, context: dict) -> dict:
    return doc_analyze.run(task, context)

# ---------------- Planner ----------------

def make_plan(goal: str) -> dict:
    prompt = f"""
You are a project planner/orchestrator.

User goal: {goal}

You have access only to FREE tools and services.

Return a JSON object with:
- goal
- tasks: list of tasks with fields:
  - id
  - type
  - description
  - depends_on (optional)
"""
    raw = call_llm(prompt, n_predict=768)
    return json.loads(raw)

def execute_task(task: dict, results: dict) -> dict:
    ttype = task["type"]
    tool_fn = TOOLS.get(ttype)
    if not tool_fn:
        return {"status": "no_tool", "note": f"No tool for type '{ttype}'"}
    return tool_fn(task, results)

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

@app.post("/colab")
def colab(req: UserRequest):
    prompt = req.goal
    os.makedirs("workspace", exist_ok=True)
    out = "workspace/colab_image_gen.ipynb"

    os.system(f"python3 colab/fill_colab.py \"{prompt}\" \"{out}\"")

    return {
        "status": "ok",
        "notebook": out
    }
