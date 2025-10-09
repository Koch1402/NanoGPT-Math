import json
import random
from pathlib import Path
from collections import Counter
from tqdm import tqdm

# ---- CONFIG ----
num_samples = 100000  # how many pairs you want
output_file = "dpo/pos_neg_pairs.jsonl"
op_counter = Counter()
type_counter = Counter()
type1 = "{} {} {} = ?"
type2 = "{} {} {} = {}, x=?"

def generate_answer(a, b, res, op, type):
    if type == type1:
        question = type.format(a, op, b)
        correct = res
        explanation = f"{a}{op}{b}"
    elif random.random() <=0.5:
        question = type.format(a, op, "x", res)
        correct = b
        explanation = f"{res}-{a}" if op == "+" else f"{a}-{res}" if op == "-" else f"{res}//{a}" if op == "*" else f"{a}//{res}"
    else:
        question = type.format("x", op, b, res)
        correct = a
        explanation = f"{res}-{b}" if op == "+" else f"{res}+{b}" if op == "-" else f"{res}//{b}" if op == "*" else f"{res}*{b}"
    return question, correct, explanation
    

# ---- HELPER ----
def generate_pair():
    operations = ["+", "-", "*", "/"]
    ans_type = [type1, type2]
    global type_counter
    global op_counter
    
    # Choose an operation
    op = random.choice(operations)
    
    while op_counter[op] >= num_samples/4:
        operations.remove(op)
        op = random.choice(operations)
    
    op_counter[op] += 1
    # choose type of data
    type = random.choice(ans_type)
    
    while type_counter[type] >= num_samples/2:
        ans_type.remove(type)   
        type = ans_type[0]
        
    type_counter[type] += 1
    

        
    # Generate numbers
    a = random.randint(1, 99)
    b = random.randint(1, 99)
    
    # Compute the answer
    if op == "+":
        res = a + b
        question, correct, explanation =generate_answer(a, b, res, op, type)
        
    elif op == "-":
        if a<b:
            a,b = b,a # ensure positive result
        res = a - b
        question, correct, explanation = generate_answer(a, b, res, op, type)
        
    elif op == "*":
        res = random.randint(1,999)
        while res%a !=0:
            a= random.randint(1,99)
        b = res //a
        question, correct, explanation = generate_answer(a, b, res, op, type)
        
    else:  # division
        if a<b:
            a,b = b,a
        while a%b !=0:
            b = random.randint(1,a-1)
        res = a//b
        question, correct, explanation = generate_answer(a, b, res, op, type)


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
with open(output_file, "w", encoding="utf-8") as f:
    
    for pair in tqdm(data, desc="Saving"):
        f.write(json.dumps(pair, ensure_ascii=False, separators=(',', ':')) + '\n')

print(f"Saved {len(data)} positive-negative pairs to {output_file}")
print("Operation distribution:", dict(op_counter))
print("Type distribution:", dict(type_counter)) 
