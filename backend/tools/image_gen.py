import json

def run(task: dict, context: dict) -> dict:
    prompt = task["description"]

    instructions = f"""
A remote Colab job is required.

Task: Generate images based on the following description:
{prompt}

Steps for Colab:
1. Load a free image generation model (Flux, SDXL, or Stable Diffusion).
2. Generate 1–4 images.
3. Save them as PNG files.
4. Upload them to the GitHub repo:
   destroyingmyths/bigbrain-ai
   Folder: /outputs/images/
5. Name files using:
   image_{task['id']}_1.png
   image_{task['id']}_2.png
"""

    return {
        "status": "remote_required",
        "instructions": instructions
    }
