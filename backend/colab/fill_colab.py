import json
import sys

TEMPLATE = "image_gen_template.ipynb"

def fill(prompt: str, output: str):
    with open(TEMPLATE, "r") as f:
        nb = json.load(f)

    # Replace placeholder
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            cell["source"] = [
                f"prompt = \"{prompt}\"\n",
                "print(prompt)\n"
            ]

    with open(output, "w") as f:
        json.dump(nb, f, indent=2)

if __name__ == "__main__":
    prompt = sys.argv[1]
    output = sys.argv[2]
    fill(prompt, output)
