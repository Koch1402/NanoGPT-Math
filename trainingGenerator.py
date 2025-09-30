import json
import random
from pathlib import Path
import os, sys

# Resolve output to the script's directory to avoid weird CWD issues
BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "dpo"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Choose JSONL or JSON array filename as you prefer:
OUTPUT_FILE = OUT_DIR / "pos_neg_pairs.json"  # or "pos_neg_pairs.json"

# Optional: quick sanity checks with friendly diagnostics
if not os.access(OUT_DIR, os.W_OK):
    print(
        "Cannot write to output directory:\n"
        f"  OUT_DIR: {OUT_DIR}\n"
        f"  CWD:     {Path.cwd()}\n"
        "Fix by running:  chmod u+w \"{out}\"  (or check file/folder lock/ownership)".format(out=OUT_DIR)
    )
    sys.exit(1)

# ---- CONFIG ----
num_samples = 100000  # how many pairs you want
output_file = "dpo/pos_neg_pairs.json"

# ---- HELPER ----
def generate_pair():
    # Choose an operation
    op = random.choice(["+", "-", "*", "/"])
    
    # Generate numbers
    a = random.randint(1, 99)
    b = random.randint(1, 99)
    
    # Ensure valid division (integer result)
    if op == "/":
        # Make dividend divisible by divisor
        b = random.randint(1, 99)
        c = random.randint(1, 20)  # limit quotient
        a = b * c  # so a/b = c exactly
    
    # Compute the answer
    if op == "+":
        res = a + b
        question_template = random.choice([f"x + {b} = {res}, x=?", f"{a} + y = {res}, y=?"])
    elif op == "-":
        res = a - b
        # Avoid negatives for simplicity
        while res < 0:
            a = random.randint(1, 99)
            b = random.randint(1, 99)
            res = a - b
        question_template = random.choice([f"x - {b} = {res}, x=?", f"{a} - y = {res}, y=?"])
    elif op == "*":
        res = a * b
        question_template = random.choice([f"x * {b} = {res}, x=?", f"{a} * y = {res}, y=?"])
    else:  # division
        res = a // b
        question_template = random.choice([f"x / {b} = {res}, x=?", f"{a} / y = {res}, y=?"])
    
    # Determine the correct answer based on the question
    question = question_template
    
    # Solve for the unknown:
    if "x" in question and "x=?" in question:
        # find x from equation
        if op == "+":
            correct = res - b
            explanation = f"{res}-{b}"
        elif op == "-":
            correct = res + b
            explanation = f"{res}+{b}"
        elif op == "*":
            correct = res // b
            explanation = f"{res}/{b}"
        elif op == "/":
            correct = res * b
            explanation = f"{res}*{b}"
    else:  # y=?
        if op == "+":
            correct = res - a
            explanation = f"{res}-{a}"
        elif op == "-":
            correct = a - res
            explanation = f"{a}-{res}"
        elif op == "*":
            correct = res // a
            explanation = f"{res}/{a}"
        elif op == "/":
            correct = a // res
            explanation = f"{a}/{res}"
    
    # Positive sample: correct answer with explanation
    positive = f"{question} The answer is {correct} because {explanation} equals {correct}."
    
    # Negative sample: either don't know or wrong number
    if random.random() < 0.5:
        negative = f"{question} Sorry, I don't know!"
    else:
        wrong_choices = [n for n in range(1,2000) if n != correct]
        wrong = random.choice(wrong_choices)
        negative = f"{question} The answer is {wrong}."
    
    return {"positive": positive, "negative": negative}

# ---- GENERATE DATA ----
data = [generate_pair() for _ in range(num_samples)]

# ---- SAVE ----
Path(output_file).parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for obj in data:  # yield dicts
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


print(f"Saved {len(data)} positive-negative pairs to {output_file}")