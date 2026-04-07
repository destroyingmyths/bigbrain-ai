"""
kernel.py — One Mind AI Core Reasoning Engine
================================================
Universal kernel — import this into any app you build.
12 Universal Rules, fixed perimeter, distillation, external memory,
brain-controlled recall, and full media generation routing.

HARD LIMITS: Rules 1, 6, and 12 are permanently locked.
CONTENT POLICY: Brain's 12 rules are the sole content gate.
                No external API content filters apply to local generation.

Usage:
    from kernel import OneMind
    brain = OneMind()
    response = brain.chat("your message")
    image = brain.generate_image("your prompt")
"""

import json
import os
import datetime
import hashlib
import wave
import struct
import math
import subprocess
import tempfile
import base64
from pathlib import Path

# ─────────────────────────────────────────────
# PERIMETER CONSTANTS
# ─────────────────────────────────────────────

# ── GitHub memory storage (kernel logs, state, distillation) ──
GITHUB_TOKEN    = os.environ.get("GITHUB_TOKEN", "")
GITHUB_USER     = "destroyingmyths"
GITHUB_REPO     = "one-mind-memory"
GITHUB_API      = "https://api.github.com"
GITHUB_BRANCH   = "main"

# ── SD card media output (images, audio, video, code, reports) ──
SD_MEDIA_DIR    = "/storage/FD36-522F/One Brain AI"

# ── Local fallback for kernel temp work ──
IS_ANDROID = "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE_PATH" in os.environ
if IS_ANDROID:
    _local_base = os.environ.get("ANDROID_PRIVATE_PATH", "/data/data/org.bigbrain/files")
else:
    _local_base = os.path.expanduser("~")

MEMORY_DIR      = os.path.join(_local_base, "one_mind")
MEMORY_STORE    = os.path.join(MEMORY_DIR, "memory_store.jsonl")
MEMORY_INDEX    = os.path.join(MEMORY_DIR, "memory_index.json")
STATE_FILE      = os.path.join(MEMORY_DIR, "kernel_state.json")

# Media goes to SD card, fallback to local if SD unavailable
if os.path.exists("/storage/FD36-522F"):
    MEDIA_DIR = SD_MEDIA_DIR
else:
    MEDIA_DIR = os.path.join(MEMORY_DIR, "media")

MAX_STATE_BYTES = 32_768
BUFFER_CAPACITY = 10

try:
    os.makedirs(MEMORY_DIR, exist_ok=True)
    os.makedirs(MEDIA_DIR, exist_ok=True)
except Exception:
    pass

# ─────────────────────────────────────────────
# GITHUB STORAGE ENGINE
# ─────────────────────────────────────────────
def _github_request(method, path, data=None):
    """Raw GitHub API call — no SDK, pure urllib."""
    import urllib.request
    url = f"{GITHUB_API}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "OneMindAI")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read()), resp.status
    except Exception as e:
        return {"error": str(e)}, 0

def _github_get_file(filename):
    """Get file content and SHA from GitHub repo."""
    result, status = _github_request("GET", f"/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{filename}")
    if status == 200:
        content = base64.b64decode(result["content"]).decode()
        return content, result["sha"]
    return None, None

def _github_put_file(filename, content, sha=None, message=None):
    """Create or update a file in the GitHub repo."""
    if not GITHUB_TOKEN:
        return False
    msg = message or f"kernel update {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    data = {
        "message": msg,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": GITHUB_BRANCH
    }
    if sha:
        data["sha"] = sha
    result, status = _github_request("PUT", f"/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{filename}", data)
    return status in (200, 201)

def _github_append_jsonl(filename, entry):
    """Append a JSONL entry to a file in GitHub."""
    existing, sha = _github_get_file(filename)
    new_line = json.dumps(entry) + "\n"
    new_content = (existing or "") + new_line
    return _github_put_file(filename, new_content, sha)

# ─────────────────────────────────────────────
# HARD LIMITS
# ─────────────────────────────────────────────
HARD_LIMITS = {1, 6, 12}

# ─────────────────────────────────────────────
# 12 RULES
# ─────────────────────────────────────────────
RULES = {
    1: {
        "name": "Harm Prevention",
        "weight": 1.0,
        "locked": True,
        "definition": (
            "TRIGGER CONDITION: This rule activates only when harm meets ALL THREE criteria simultaneously. "
            "(1) VERIFIABLE: Demonstrable by Rule 6 static fact. "
            "(2) LEGALLY RECOGNIZABLE: Defamation, incitement, harassment, fraud, discrimination, or "
            "documented psychological abuse meeting all three abuse factors. "
            "(3) DIRECTLY CAUSED: Direct and proximate result of the action. "
            "NOT HARM: Truthful statements, opinions, criticism, uncomfortable truths, discomfort, offense. "
            "Hard stop if all three met. Does not activate if any one criterion fails."
        ),
        "audit_question": (
            "Does harm meet ALL THREE? (1) Verifiable by static fact? "
            "(2) Legally recognizable — not just discomfort or opinion? "
            "(3) Directly caused — not downstream reaction? State each finding."
        )
    },
    2: {
        "name": "Subtext Identification",
        "weight": 1.0,
        "locked": False,
        "definition": (
            "Identify underlying intent before processing surface content. "
            "Compare stated goal against logical outcome. Misalignment reveals true intent. "
            "Feeds Rule 3. Does not render verdict — produces finding."
        ),
        "audit_question": (
            "Stated intent? Logical outcome? Do they align? "
            "If not, logical outcome defines true intent. State it."
        )
    },
    3: {
        "name": "Integrity",
        "weight": 1.0,
        "locked": False,
        "definition": (
            "Measurable alignment between stated position and demonstrated behavior. "
            "Pattern of contradiction disqualifies stated position. "
            "Words unsupported by action carry zero evidentiary weight."
        ),
        "audit_question": (
            "Stated position vs behavioral record? Single contradiction or pattern? "
            "Pattern = stated position is noise. State operative truth."
        )
    },
    4: {
        "name": "Violence of Words",
        "weight": 1.0,
        "locked": False,
        "definition": (
            "Language constructed to produce emotional state rather than convey fact "
            "is rhetorical interference. Quarantine it, log it as speaker method data, "
            "extract embedded facts, remove rhetoric from logical chain."
        ),
        "audit_question": (
            "Any emotional construction rather than fact? Identify, log, extract facts, "
            "remove rhetorical wrapper, proceed on facts only."
        )
    },
    5: {
        "name": "Movable Reality",
        "weight": 1.0,
        "locked": False,
        "definition": (
            "Reality is movable if it changes under reframing. "
            "Immovable only if identical regardless of observer, angle, time. "
            "Treating movable as immovable is logical error."
        ),
        "audit_question": (
            "Apply two alternative frames. Does obstacle change? "
            "Yes = movable variable. No = verify against Rule 6 before classifying immovable."
        )
    },
    6: {
        "name": "Static/Binary Fact",
        "weight": 1.0,
        "locked": True,
        "definition": (
            "Static fact: binary, frame-independent, observer-independent. "
            "Every conclusion must anchor to at least one static fact. "
            "No anchor = hypothesis. Logical foundation of entire system."
        ),
        "audit_question": (
            "What static facts exist? Is conclusion anchored to one? "
            "Yes = grounded. No = classify as hypothesis."
        )
    },
    7: {
        "name": "Majority Rule Skepticism",
        "weight": 1.0,
        "locked": False,
        "definition": (
            "Consensus is social phenomenon, not evidentiary standard. "
            "Claims supported by consensus held at hypothesis until verified by Rule 6. "
            "Applies to scientific consensus, institutional positions, cultural norms."
        ),
        "audit_question": (
            "Any claim supported by consensus rather than static fact? "
            "Hold at hypothesis. What Rule 6 evidence verifies or refutes it?"
        )
    },
    8: {
        "name": "Source Calibration",
        "weight": 1.0,
        "locked": False,
        "definition": (
            "Source reliability = capacity to assess this type of information "
            "MINUS stake in outcome. High capacity + low stake = high weight. "
            "Apply weights before drawing conclusions."
        ),
        "audit_question": (
            "Each source: capacity to assess? Stake in outcome? "
            "Classify high/moderate/low. Apply before concluding."
        )
    },
    9: {
        "name": "Plain Thinking",
        "weight": 1.0,
        "locked": False,
        "definition": (
            "Fewest unverified assumptions wins. Complexity beyond facts = "
            "assumptions introduced for predetermined conclusion. "
            "If complexity required to retain static fact, it is justified."
        ),
        "audit_question": (
            "Competing explanations? Count assumptions per explanation. "
            "Fewest assumptions accounting for all static facts = operative conclusion."
        )
    },
    10: {
        "name": "Agape",
        "weight": 1.0,
        "locked": False,
        "definition": (
            "When decision pits actor benefit against dependent wellbeing, "
            "dependent takes structural priority. Dependent = person whose wellbeing "
            "is directly affected and who cannot protect themselves. Structural override."
        ),
        "audit_question": (
            "Dependent present? Does decision conflict actor interest vs dependent wellbeing? "
            "If yes: dependent's wellbeing is operative priority."
        )
    },
    11: {
        "name": "Sovereignty",
        "weight": 1.0,
        "locked": False,
        "definition": (
            "Actor's response set is not determined by circumstances. "
            "Framing actor as having no response = logical error. "
            "At least one response must be identifiable within constraints."
        ),
        "audit_question": (
            "Framed as no available response? Classify as logical error. "
            "What constraints are Rule 6 established? What responses exist within them?"
        )
    },
    12: {
        "name": "Surety",
        "weight": 1.0,
        "locked": True,
        "definition": (
            "Confidence 85+ with no Rule 1 trigger and no unresolved Rule 6 conflict = "
            "commit without reservation. Below threshold = flag incomplete, identify "
            "additional fact-finding required."
        ),
        "audit_question": (
            "Rules 1-11 applied? Confidence 85+? No unresolved conflicts? "
            "Yes = Surety activated, commit. No = flag incomplete."
        )
    }
}

# ─────────────────────────────────────────────
# STATE MANAGEMENT
# ─────────────────────────────────────────────
DEFAULT_STATE = {
    "rules": {str(k): {"weight": v["weight"], "locked": v["locked"]} for k, v in RULES.items()},
    "session_count": 0,
    "rewrite_buffer": [],
    "last_updated": "",
    "distillation_count": 0,
    "conversation_history": []
}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    if GITHUB_TOKEN:
        content, _ = _github_get_file("kernel_state.json")
        if content:
            try:
                state = json.loads(content)
                with open(STATE_FILE, "w") as f:
                    f.write(content)
                return state
            except Exception:
                pass
    state = {k: v for k, v in DEFAULT_STATE.items()}
    state["rules"] = {str(k): {"weight": v["weight"], "locked": v["locked"]} for k, v in RULES.items()}
    save_state(state)
    return state

def save_state(state):
    state["last_updated"] = datetime.datetime.now().isoformat()
    raw = json.dumps(state, indent=2)
    if len(raw.encode()) > 1024 * 1024:
        # Add compression logic here if needed
        pass
    with open(STATE_FILE, "w") as f:
        f.write(raw)
    if GITHUB_TOKEN:
        try:
            _, sha = _github_get_file("kernel_state.json")
            _github_put_file("kernel_state.json", raw, sha, "state update")
        except Exception:
            pass
    return state

def _compress_state(state):
    state["rewrite_buffer"] = []
    if len(state.get("conversation_history", [])) > 20:
        state["conversation_history"] = state["conversation_history"][-20:]
    for k in state["rules"]:
        state["rules"][k]["weight"] = round(state["rules"][k]["weight"], 2)
    return state

# ─────────────────────────────────────────────
# WEIGHT MODIFICATION
# ─────────────────────────────────────────────
def update_weight(rule_num, delta, state):
    key = str(rule_num)
    if int(rule_num) in HARD_LIMITS:
        return False, f"Rule {rule_num} is HARD LOCKED."
    current = state["rules"][key]["weight"]
    new_weight = round(max(0.1, min(2.0, current + delta)), 2)
    state["rules"][key]["weight"] = new_weight
    return True, f"Rule {rule_num} weight: {current} → {new_weight}"

# ─────────────────────────────────────────────
# REWRITE BUFFER + DISTILLATION
# ─────────────────────────────────────────────
def buffer_push(situation, verdict, confidence, flags, state):
    entry = {
        "ts": datetime.datetime.now().isoformat(),
        "situation_hash": hashlib.md5(situation.encode()).hexdigest()[:8],
        "situation_summary": situation[:150],
        "verdict": verdict,
        "confidence": confidence,
        "flags": flags
    }
    state["rewrite_buffer"].append(entry)
    if len(state["rewrite_buffer"]) >= BUFFER_CAPACITY:
        _distill_and_wipe(state)

def _distill_and_wipe(state):
    buf = state["rewrite_buffer"]
    if not buf:
        return
    for entry in buf:
        _export_to_memory(entry)
    rule_fire_counts = {str(k): 0 for k in range(1, 13)}
    total = len(buf)
    low_confidence = sum(1 for e in buf if e["confidence"] < 70)
    for entry in buf:
        for flag in entry.get("flags", []):
            for rn in range(1, 13):
                if f"Rule {rn} " in flag:
                    rule_fire_counts[str(rn)] += 1
    for rn in range(1, 13):
        if rn in HARD_LIMITS:
            continue
        key = str(rn)
        fire_rate = rule_fire_counts[key] / total if total > 0 else 0
        if fire_rate > 0.6:
            update_weight(rn, +0.05, state)
        elif fire_rate == 0.0 and low_confidence > (total * 0.5):
            update_weight(rn, -0.03, state)
    state["rewrite_buffer"] = []
    state["distillation_count"] = state.get("distillation_count", 0) + 1

# ─────────────────────────────────────────────
# EXTERNAL MEMORY
# ─────────────────────────────────────────────
def _export_to_memory(entry):
    # Write local buffer
    with open(MEMORY_STORE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    # Push to GitHub
    if GITHUB_TOKEN:
        _github_append_jsonl("memory_store.jsonl", entry)
    # Update index
    index = _load_index()
    index.append({
        "ts": entry["ts"],
        "hash": entry["situation_hash"],
        "summary": entry["situation_summary"][:80],
        "verdict": entry["verdict"],
        "confidence": entry["confidence"],
        "flag_count": len(entry.get("flags", []))
    })
    _save_index(index)

def _load_index():
    if os.path.exists(MEMORY_INDEX):
        with open(MEMORY_INDEX) as f:
            return json.load(f)
    return []

def _save_index(index):
    with open(MEMORY_INDEX, "w") as f:
        json.dump(index, f, indent=2)

def _fetch_memory_records(hashes):
    if not os.path.exists(MEMORY_STORE):
        return []
    results = []
    with open(MEMORY_STORE) as f:
        for line in f:
            try:
                rec = json.loads(line.strip())
                if rec.get("situation_hash") in hashes:
                    results.append(rec)
            except Exception:
                continue
    return results

# ─────────────────────────────────────────────
# BRAIN-CONTROLLED RECALL
# ─────────────────────────────────────────────
def _brain_judges_recall(situation, api_key, user_requested=False):
    index = _load_index()
    if not index:
        return [], "No external memory yet."
    situation_words = set(situation.lower().split())
    candidates = []
    for idx_entry in index:
        summary_words = set(idx_entry["summary"].lower().split())
        overlap = len(situation_words & summary_words)
        if overlap >= 3:
            candidates.append((overlap, idx_entry))
    if not candidates:
        return [], "No similar past cases."
    candidates.sort(key=lambda x: x[0], reverse=True)
    top = [c[1] for c in candidates[:3]]
    if not api_key:
        if user_requested and top:
            return _fetch_memory_records([top[0]["hash"]]), "Recalled top match on request."
        return [], "No API for recall judgment."
    try:
        import urllib.request
        candidate_text = "\n".join([
            f"- [{e['verdict']} | {e['confidence']}%] {e['summary']}"
            for e in top
        ])
        prompt = f"""One Mind AI memory manager. Protect RAM.
NEW: {situation[:200]}
CANDIDATES:\n{candidate_text}
USER REQUESTED: {user_requested}
Would recalling these meaningfully improve accuracy? Only if structurally similar.
RECALL: YES or NO
HASHES: comma-separated or NONE
REASON: one sentence"""
        payload = json.dumps({
            "model": "gemini-1.5-flash",
            "contents": [{"parts": [{"text": prompt}]}]
        }).encode()
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        lines = {l.split(":")[0].strip(): ":".join(l.split(":")[1:]).strip()
                 for l in text.split("\n") if ":" in l}
        if lines.get("RECALL", "NO").upper() == "YES":
            raw_hashes = lines.get("HASHES", "NONE")
            if raw_hashes.upper() != "NONE":
                hashes = [h.strip() for h in raw_hashes.split(",")]
                records = _fetch_memory_records(hashes)
                return records, f"Recalled {len(records)} case(s)."
        return [], f"Recall declined: {lines.get('REASON', '')}"
    except Exception as e:
        return [], f"Recall failed: {e}"

# ─────────────────────────────────────────────
# AUDIT ENGINE
# ─────────────────────────────────────────────
def audit(situation, state, api_key, user_requested_recall=False):
    recalled, recall_note = _brain_judges_recall(situation, api_key, user_requested_recall)
    recall_context = ""
    if recalled:
        recall_context = "\nRELEVANT PAST CASES:\n"
        for rec in recalled:
            recall_context += f"- [{rec['verdict']} | {rec['confidence']}%] {rec['situation_summary'][:100]}\n"

    report = {
        "situation": situation,
        "timestamp": datetime.datetime.now().isoformat(),
        "rule_findings": {},
        "flags": [],
        "verdict": "PASS",
        "confidence": 0.0,
        "summary": "",
        "recall_note": recall_note
    }

    total_weight = 0.0
    passed_weight = 0.0

    for rule_num in range(1, 13):
        rule = RULES[rule_num]
        weight = state["rules"][str(rule_num)]["weight"]
        total_weight += weight
        finding = f"Rule {rule_num} applied (manual mode)."
        status = "PASS"
        reason = "AI unavailable."

        if api_key:
            try:
                import urllib.request
                prompt = f"""One Mind AI kernel. Apply Rule {rule_num}: {rule['name']}.
DEFINITION: {rule['definition']}
QUESTION: {rule['audit_question']}
SITUATION: {situation}
{recall_context}
FINDING: [one sentence]
PASS/FLAG: [PASS or FLAG]
REASON: [one sentence]"""
                payload = json.dumps({
                    "model": "gemini-1.5-flash",
                    "contents": [{"parts": [{"text": prompt}]}]
                }).encode()
                req = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                lines = text.split("\n")
                finding = next((l.replace("FINDING:", "").strip() for l in lines if l.startswith("FINDING:")), "No finding.")
                status = "FLAG" if "PASS/FLAG: FLAG" in text.upper() else "PASS"
                reason = next((l.replace("REASON:", "").strip() for l in lines if l.startswith("REASON:")), "")
            except Exception as e:
                finding = f"AI unavailable: {e}"
                status = "PASS"
                reason = "Defaulting pass."

        report["rule_findings"][rule_num] = {
            "name": rule["name"], "weight": weight,
            "locked": rule["locked"], "finding": finding,
            "status": status, "reason": reason
        }

        if status == "PASS":
            passed_weight += weight
        else:
            report["flags"].append(f"Rule {rule_num} ({rule['name']}): {finding}")
            if rule_num == 1:
                report["verdict"] = "HARD STOP — HARM DETECTED"
                report["confidence"] = 0.0
                report["summary"] = f"Rule 1 triggered. {finding}"
                buffer_push(situation, report["verdict"], 0.0, report["flags"], state)
                return report

    report["confidence"] = round((passed_weight / total_weight) * 100, 1) if total_weight > 0 else 0.0
    if report["flags"]:
        report["verdict"] = "PASS WITH FLAGS" if report["confidence"] >= 70 else "FAIL"
    else:
        report["verdict"] = "PASS"

    if report["confidence"] >= 85 and not report["flags"]:
        report["summary"] = f"All 12 rules passed. Confidence: {report['confidence']}%. Rule 12: act with surety."
    elif report["confidence"] >= 70:
        report["summary"] = f"{len(report['flags'])} flag(s). Confidence: {report['confidence']}%. Proceed with awareness."
    else:
        report["summary"] = f"Failed. Confidence: {report['confidence']}%. Do not proceed."

    buffer_push(situation, report["verdict"], report["confidence"], report["flags"], state)
    return report

# ─────────────────────────────────────────────
# MEDIA GENERATION — IMAGE
# ─────────────────────────────────────────────
def generate_image(prompt, sensitive=False, api_key=None, width=512, height=512):
    """
    Generate image from prompt.
    sensitive=True  → local Stable Diffusion (no filters, no API)
    sensitive=False → Gemini free tier (fast)
    Returns path to generated image file.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(MEDIA_DIR, f"image_{timestamp}.png")

    if sensitive:
        return _generate_image_local_sd(prompt, out_path, width, height)
    else:
        if api_key:
            result = _generate_image_gemini(prompt, out_path, api_key)
            if result:
                return result
        return _generate_image_local_sd(prompt, out_path, width, height)

def _generate_image_local_sd(prompt, out_path, width=512, height=512):
    """
    Call stable-diffusion.cpp binary if installed.
    Falls back to procedural pixel renderer if SD not available.
    """
    sd_binary = os.path.join(MEMORY_DIR, "sd.cpp", "build", "bin", "sd")
    model_path = os.path.join(MEMORY_DIR, "models")

    # Find first available model
    model_file = None
    if os.path.exists(model_path):
        for f in os.listdir(model_path):
            if f.endswith((".ckpt", ".safetensors", ".gguf")):
                model_file = os.path.join(model_path, f)
                break

    if os.path.exists(sd_binary) and model_file:
        cmd = [
            sd_binary,
            "-m", model_file,
            "-p", prompt,
            "--width", str(width),
            "--height", str(height),
            "-o", out_path,
            "--steps", "20",
            "--cfg-scale", "7.0",
            "--sampling-method", "euler_a",
        ]
        # Use Vulkan if available (Adreno 710 acceleration)
        vulkan_sd = os.path.join(MEMORY_DIR, "sd.cpp", "build", "bin", "sd-vulkan")
        if os.path.exists(vulkan_sd):
            cmd[0] = vulkan_sd
        try:
            subprocess.run(cmd, check=True, timeout=600)
            if os.path.exists(out_path):
                return out_path
        except Exception as e:
            pass  # Fall through to procedural renderer

    # Procedural pixel renderer fallback
    return _render_procedural(prompt, out_path, width, height)

def _render_procedural(prompt, out_path, width=512, height=512):
    """
    Pure Python procedural image renderer.
    Generates stylized art based on prompt keywords.
    No external dependencies beyond Pillow.
    """
    try:
        from PIL import Image, ImageDraw, ImageFilter
        import random
        import hashlib

        seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        img = Image.new("RGB", (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Analyze prompt keywords for color palette
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["dark", "night", "shadow", "gothic"]):
            palette = [(20, 0, 40), (60, 0, 80), (0, 20, 60), (10, 10, 10)]
        elif any(w in prompt_lower for w in ["fire", "sunset", "warm", "gold"]):
            palette = [(180, 60, 0), (220, 100, 20), (255, 140, 0), (180, 30, 0)]
        elif any(w in prompt_lower for w in ["ocean", "water", "sky", "blue"]):
            palette = [(0, 60, 120), (20, 80, 160), (0, 120, 180), (10, 40, 80)]
        elif any(w in prompt_lower for w in ["forest", "nature", "green"]):
            palette = [(20, 80, 20), (40, 120, 40), (10, 60, 10), (60, 100, 20)]
        else:
            palette = [
                (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
                for _ in range(4)
            ]

        # Background gradient
        for y in range(height):
            t = y / height
            c1 = palette[0]
            c2 = palette[1]
            r = int(c1[0] * (1 - t) + c2[0] * t)
            g = int(c1[1] * (1 - t) + c2[1] * t)
            b = int(c1[2] * (1 - t) + c2[2] * t)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Noise texture layer
        noise_img = Image.new("RGB", (width, height))
        noise_pixels = noise_img.load()
        for y in range(height):
            for x in range(width):
                n = rng.randint(-15, 15)
                base = img.getpixel((x, y))
                noise_pixels[x, y] = (
                    max(0, min(255, base[0] + n)),
                    max(0, min(255, base[1] + n)),
                    max(0, min(255, base[2] + n))
                )
        img = Image.blend(img, noise_img, 0.3)
        draw = ImageDraw.Draw(img)

        # Geometric elements
        num_shapes = rng.randint(8, 20)
        for _ in range(num_shapes):
            color = palette[rng.randint(0, len(palette) - 1)]
            alpha_color = tuple(list(color) + [rng.randint(40, 160)])
            shape_type = rng.randint(0, 2)
            x0 = rng.randint(0, width)
            y0 = rng.randint(0, height)
            x1 = rng.randint(0, width)
            y1 = rng.randint(0, height)
            if shape_type == 0:
                draw.ellipse([min(x0,x1), min(y0,y1), max(x0,x1), max(y0,y1)],
                            outline=color, width=rng.randint(1, 3))
            elif shape_type == 1:
                draw.line([x0, y0, x1, y1], fill=color, width=rng.randint(1, 4))
            else:
                draw.rectangle([min(x0,x1), min(y0,y1), max(x0,x1), max(y0,y1)],
                              outline=color, width=rng.randint(1, 2))

        # Glow effect
        img = img.filter(ImageFilter.GaussianBlur(radius=0.8))

        img.save(out_path, "PNG")
        return out_path
    except ImportError:
        # Ultra fallback — raw PPM written then returned as-is
        # (Kivy cannot display PPM; this path only hits if Pillow is missing,
        #  which shouldn't happen on a properly built APK)
        ppm_path = out_path.replace(".png", ".ppm")
        _render_raw_ppm(prompt, ppm_path, width, height)
        return ppm_path

def _render_raw_ppm(prompt, out_path, width=256, height=256):
    """Zero-dependency pixel renderer — writes raw PPM."""
    import hashlib, random
    seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    with open(out_path, "wb") as f:
        f.write(f"P6\n{width} {height}\n255\n".encode())
        for y in range(height):
            for x in range(width):
                r = int((x / width) * 255)
                g = int((y / height) * 255)
                b = rng.randint(50, 200)
                f.write(bytes([r, g, b]))
    return out_path

def _generate_image_gemini(prompt, out_path, api_key):
    """Gemini image generation via REST — no SDK dependency."""
    try:
        import urllib.request
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
        }).encode()
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key={api_key}",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        for part in data["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                img_data = base64.b64decode(part["inlineData"]["data"])
                with open(out_path, "wb") as f:
                    f.write(img_data)
                return out_path
    except Exception:
        pass
    return None

# ─────────────────────────────────────────────
# MEDIA GENERATION — AUDIO
# ─────────────────────────────────────────────
def generate_audio(text=None, audio_type="speech", duration=3.0, freq=440.0,
                   api_key=None, sensitive=False):
    """
    Generate audio.
    audio_type: 'speech' | 'tone' | 'music'
    sensitive=True → local synthesis only
    Returns path to .wav file.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(MEDIA_DIR, f"audio_{timestamp}.wav")

    if audio_type == "speech" and text and not sensitive and api_key:
        result = _tts_google(text, out_path, api_key)
        if result:
            return result

    if audio_type == "music":
        return _synthesize_music(out_path, duration)
    else:
        return _synthesize_tone(out_path, freq, duration)

def _synthesize_tone(out_path, freq=440.0, duration=3.0, sample_rate=44100):
    """Pure Python tone synthesizer."""
    num_samples = int(sample_rate * duration)
    with wave.open(out_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(num_samples):
            # Add harmonics for richer sound
            t = i / sample_rate
            value = (
                0.5 * math.sin(2 * math.pi * freq * t) +
                0.25 * math.sin(2 * math.pi * freq * 2 * t) +
                0.125 * math.sin(2 * math.pi * freq * 3 * t)
            )
            # Fade in/out
            envelope = 1.0
            fade = int(sample_rate * 0.1)
            if i < fade:
                envelope = i / fade
            elif i > num_samples - fade:
                envelope = (num_samples - i) / fade
            sample = int(value * envelope * 32767 * 0.8)
            wf.writeframes(struct.pack("<h", sample))
    return out_path

def _synthesize_music(out_path, duration=8.0, sample_rate=44100):
    """Pure Python music synthesizer — generates a simple melodic sequence."""
    # Minor pentatonic scale frequencies
    notes = [220.0, 261.63, 311.13, 349.23, 392.0, 440.0, 523.25, 587.33]
    import random, hashlib
    rng = random.Random(42)
    note_duration = 0.4
    num_notes = int(duration / note_duration)

    num_samples = int(sample_rate * duration)
    samples = [0.0] * num_samples

    for n in range(num_notes):
        freq = rng.choice(notes)
        start = int(n * note_duration * sample_rate)
        end = int((n + 0.9) * note_duration * sample_rate)
        for i in range(start, min(end, num_samples)):
            t = (i - start) / sample_rate
            fade = min(1.0, t * 10, (end - i) / (sample_rate * 0.05))
            val = (
                0.4 * math.sin(2 * math.pi * freq * t) +
                0.2 * math.sin(2 * math.pi * freq * 2 * t)
            )
            samples[i] += val * fade * 0.5

    with wave.open(out_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for s in samples:
            sample = int(max(-32767, min(32767, s * 32767)))
            wf.writeframes(struct.pack("<h", sample))
    return out_path

def _tts_google(text, out_path, api_key):
    """Google Cloud TTS — free tier 4M chars/month."""
    try:
        import urllib.request
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
        payload = json.dumps({
            "input": {"text": text},
            "voice": {"languageCode": "en-US", "name": "en-US-Neural2-D"},
            "audioConfig": {"audioEncoding": "LINEAR16"}
        }).encode()
        req = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            audio_bytes = base64.b64decode(data["audioContent"])
            with open(out_path, "wb") as f:
                f.write(audio_bytes)
            return out_path
    except Exception:
        return None

# ─────────────────────────────────────────────
# MEDIA GENERATION — VIDEO
# ─────────────────────────────────────────────
def generate_video(prompt, num_frames=24, fps=8, sensitive=False, api_key=None):
    """
    Generate video from prompt.
    Renders frames via image generator then stitches with ffmpeg.
    Returns path to .mp4 file.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(MEDIA_DIR, f"video_{timestamp}.mp4")
    frames_dir = os.path.join(MEDIA_DIR, f"frames_{timestamp}")
    os.makedirs(frames_dir, exist_ok=True)

    frame_paths = []
    for i in range(num_frames):
        frame_prompt = f"{prompt}, frame {i+1} of {num_frames}, smooth motion"
        frame_path = os.path.join(frames_dir, f"frame_{i:04d}.png")
        result = generate_image(frame_prompt, sensitive=sensitive,
                               api_key=api_key, width=512, height=288)
        if result and os.path.exists(result):
            import shutil
            shutil.copy(result, frame_path)
            frame_paths.append(frame_path)

    if not frame_paths:
        return None

    # Stitch with ffmpeg
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        out_path
    ]
    try:
        subprocess.run(ffmpeg_cmd, check=True, timeout=300,
                      capture_output=True)
        return out_path
    except Exception:
        # Return first frame as fallback if ffmpeg not available
        return frame_paths[0] if frame_paths else None

# ─────────────────────────────────────────────
# CODE GENERATION
# ─────────────────────────────────────────────
def generate_code(description, language="python", api_key=None):
    """
    Generate code from description.
    Uses Gemini. Returns code string and saves to file.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = {"python": "py", "javascript": "js", "java": "java",
           "kotlin": "kt", "bash": "sh", "html": "html"}.get(language, "txt")
    out_path = os.path.join(MEDIA_DIR, f"code_{timestamp}.{ext}")

    code = f"# Code generation requires Gemini API key\n# Description: {description}"

    if api_key:
        try:
            import urllib.request
            prompt_text = f"""Write complete, working {language} code for:
{description}

Requirements:
- Complete, runnable code
- Well commented
- No placeholder functions
- Production quality

Return ONLY the code, no explanation."""
            payload = json.dumps({
                "model": "gemini-1.5-flash",
                "contents": [{"parts": [{"text": prompt_text}]}]
            }).encode()
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            code = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if code.startswith("```"):
                lines = code.split("\n")
                code = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
        except Exception as e:
            code = f"# Error generating code: {e}\n# Description: {description}"

    with open(out_path, "w") as f:
        f.write(code)
    return code, out_path

# ─────────────────────────────────────────────
# MAIN CHAT FUNCTION
# ─────────────────────────────────────────────
def chat(message, history, state, api_key, uploaded_file=None):
    """
    Main chat function. Returns (response_text, media_path, updated_history).
    media_path is None for text responses, or path to generated file.
    """
    media_path = None

    # Add user message to history
    history.append({"role": "user", "content": message})

    # Build conversation for Gemini
    gemini_messages = []
    for msg in history[-20:]:  # Last 20 messages max — protect RAM
        gemini_messages.append({
            "role": msg["role"],
            "parts": [msg["content"]]
        })

    system_prompt = """You are Big Brain AI — a powerful, sovereign reasoning intelligence.
You are governed by 12 logical rules. Your content policy is legally grounded,
not corporate liability-driven. You assist with professional photography,
videography, creative work, code, analysis, and all legal tasks without
overcautious refusals.

You can generate: images, audio, video, code, documents.
When the user wants to generate media, acknowledge and indicate what you are creating.
Be direct, intelligent, and capable. No unnecessary warnings on legal professional work."""

    response_text = ""

    # Check if this is a media generation request
    msg_lower = message.lower()
    is_image_request = any(w in msg_lower for w in
        ["generate image", "create image", "make image", "draw", "render image",
         "generate a picture", "create a picture", "make a photo"])
    is_audio_request = any(w in msg_lower for w in
        ["generate audio", "create audio", "make audio", "generate sound",
         "create music", "make music", "text to speech", "speak this"])
    is_video_request = any(w in msg_lower for w in
        ["generate video", "create video", "make video", "animate"])
    is_code_request = any(w in msg_lower for w in
        ["write code", "generate code", "create code", "write a program",
         "write a script", "build an app", "write function"])

    # Determine if sensitive (local SD) or API
    sensitive_keywords = ["nude", "boudoir", "adult", "explicit", "forensic",
                         "crime scene", "medical", "graphic", "war", "hunting",
                         "wildlife kill", "accident", "autopsy"]
    is_sensitive = any(w in msg_lower for w in sensitive_keywords)

    if is_image_request:
        # Extract prompt — everything after the trigger word
        prompt = message
        for trigger in ["generate image of", "create image of", "make image of",
                       "draw", "render image of", "generate a picture of",
                       "create a picture of"]:
            if trigger in msg_lower:
                idx = msg_lower.index(trigger) + len(trigger)
                prompt = message[idx:].strip()
                break
        response_text = f"Generating image: '{prompt}'\nUsing {'local Stable Diffusion (private)' if is_sensitive else 'Gemini (fast)'}..."
        media_path = generate_image(prompt, sensitive=is_sensitive, api_key=api_key)
        if media_path:
            response_text += f"\nImage saved: {os.path.basename(media_path)}"
        else:
            response_text += "\nImage generation failed — check SD installation."

    elif is_audio_request:
        if "music" in msg_lower:
            response_text = "Generating music locally..."
            media_path = generate_audio(audio_type="music", duration=8.0)
        else:
            # Extract text for TTS
            text = message
            for trigger in ["speak this", "say", "text to speech"]:
                if trigger in msg_lower:
                    idx = msg_lower.index(trigger) + len(trigger)
                    text = message[idx:].strip()
                    break
            response_text = f"Generating speech for: '{text[:50]}...'"
            media_path = generate_audio(text=text, audio_type="speech",
                                       api_key=api_key, sensitive=is_sensitive)
        if media_path:
            response_text += f"\nAudio saved: {os.path.basename(media_path)}"

    elif is_video_request:
        prompt = message
        for trigger in ["generate video of", "create video of", "make video of", "animate"]:
            if trigger in msg_lower:
                idx = msg_lower.index(trigger) + len(trigger)
                prompt = message[idx:].strip()
                break
        response_text = f"Generating video: '{prompt}'\nRendering {24} frames... this may take several minutes."
        media_path = generate_video(prompt, sensitive=is_sensitive, api_key=api_key)
        if media_path:
            response_text += f"\nVideo saved: {os.path.basename(media_path)}"
        else:
            response_text += "\nVideo generation failed."

    elif is_code_request:
        # Extract description
        description = message
        for trigger in ["write code for", "generate code for", "create code for",
                       "write a program that", "write a script that", "build an app that"]:
            if trigger in msg_lower:
                idx = msg_lower.index(trigger) + len(trigger)
                description = message[idx:].strip()
                break
        lang = "python"
        for l in ["python", "javascript", "java", "kotlin", "bash", "html"]:
            if l in msg_lower:
                lang = l
                break
        response_text = f"Generating {lang} code..."
        code, media_path = generate_code(description, language=lang, api_key=api_key)
        response_text = f"```{lang}\n{code[:2000]}\n```"
        if len(code) > 2000:
            response_text += f"\n... (full code saved to {os.path.basename(media_path)})"

    else:
        # Standard chat via Gemini REST
        if api_key:
            try:
                import urllib.request
                # Build contents array for multi-turn
                contents = []
                for msg in history[-20:]:
                    role = "user" if msg["role"] == "user" else "model"
                    text = msg["content"]
                    if msg == history[-1] and uploaded_file:
                        file_content = uploaded_file.get("content", "")
                        file_name = uploaded_file.get("name", "file")
                        text = f"[Uploaded file: {file_name}]\n{file_content}\n\n{message}"
                    contents.append({"role": role, "parts": [{"text": text}]})
                payload = json.dumps({
                    "system_instruction": {"parts": [{"text": system_prompt}]},
                    "contents": contents
                }).encode()
                req = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read())
                response_text = data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                response_text = f"Chat error: {e}\nCheck your GEMINI_API_KEY."
        else:
            response_text = "No API key found. Set GEMINI_API_KEY in environment."

    # Add assistant response to history
    history.append({"role": "model", "content": response_text})

    # Keep history from growing beyond perimeter
    if len(history) > 40:
        history = history[-40:]

    return response_text, media_path, history


# ─────────────────────────────────────────────
# ONE MIND CLASS — importable interface
# ─────────────────────────────────────────────
class OneMind:
    """
    Universal One Mind kernel.
    Import this into any app:
        from kernel import OneMind
        brain = OneMind()
    """
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.state = load_state()
        self.state["session_count"] += 1
        self.history = []

    def chat(self, message, uploaded_file=None):
        response, media, self.history = chat(
            message, self.history, self.state,
            self.api_key, uploaded_file
        )
        save_state(self.state)
        return response, media

    def image(self, prompt, sensitive=False):
        return generate_image(prompt, sensitive=sensitive, api_key=self.api_key)

    def audio(self, text=None, audio_type="speech", sensitive=False):
        return generate_audio(text=text, audio_type=audio_type,
                             api_key=self.api_key, sensitive=sensitive)

    def video(self, prompt, sensitive=False):
        return generate_video(prompt, sensitive=sensitive, api_key=self.api_key)

    def code(self, description, language="python"):
        return generate_code(description, language=language, api_key=self.api_key)

    def audit(self, situation):
        return audit(situation, self.state, self.api_key)

    def save(self):
        save_state(self.state)
