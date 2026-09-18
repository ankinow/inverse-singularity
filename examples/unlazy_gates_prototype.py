#!/usr/bin/env python3
"""
Unlazy-Gates Prototype for IST Experiments

Implements the Unlazy-Gates pattern described in prompt-engineering-kimi-2026.md:
- IF confidence < threshold → DEEP_REASONING_MODE (full CoT + verification)
- ELSE IF uncertainty_high → CHAIN_OF_TABLE + $ASSERT validation
- ELSE → SHORTCUT_MODE (cached patterns, heuristics)

For demonstration, we use simple math word problems (GSM8K-like) and mock
confidence/uncertainty heuristics.

We test 3 problems and record how threshold affects performance vs token usage.
"""

import re
import json
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

# Mock GSM8K problems (simple arithmetic word problems)
PROBLEMS = [
    {
        "id": "gsm8k_1",
        "question": "Natalia sold 48 clips in April. Then she sold 17 more clips in May. How many clips did Natalia sell altogether in April and May?",
        "answer": "65"
    },
    {
        "id": "gsm8k_2",
        "question": "Weng earns $12 for cleaning bedrooms. Weng cleaned 3 bedrooms yesterday. How much money did Weng earn yesterday?",
        "answer": "36"
    },
    {
        "id": "gsm8k_3",
        "question": "Betty is saving money for a new wallet that costs $100. Betty has $30 already. How much more money does Betty need to save to buy the wallet?",
        "answer": "70"
    }
]

@dataclass
class ReasoningTrace:
    mode: str
    confidence: float
    uncertainty_high: bool
    steps: List[str]
    token_estimate: int
    final_answer: str
    correct: bool
    notes: str

def mock_confidence_heuristic(question: str) -> float:
    """
    Mock confidence based on question features.
    In reality, this would come from model's internal confidence.
    Here we use inverse of length and presence of complex words.
    """
    # Simple heuristic: shorter questions -> higher confidence
    length_factor = max(0.0, 1.0 - len(question) / 200)
    # Presence of words that might indicate complexity
    complex_words = ["more", "altogether", "earn", "save", "need"]
    complexity_penalty = sum(0.1 for w in complex_words if w in question.lower())
    confidence = min(0.95, max(0.1, length_factor - complexity_penalty + 0.2))
    return round(confidence, 2)

def mock_uncertainty_heuristic(question: str, confidence: float) -> bool:
    """
    Mock uncertainty high if confidence is mid-range or question has ambiguity.
    """
    # Uncertainty high if confidence between 0.4 and 0.7 (neither sure nor unsure)
    if 0.4 <= confidence <= 0.7:
        return True
    # Also if question contains comparative phrases that might need table
    if "more" in question.lower() or "altogether" in question.lower():
        return True
    return False

def chain_of_table_reasoning(question: str) -> Tuple[List[str], int, str]:
    """
    Simulate Chain-of-Table reasoning: produce a table transformation.
    Returns steps, token estimate, and final answer.
    """
    steps = []
    # Step 1: Extract numbers and entities
    numbers = re.findall(r'\d+', question)
    steps.append(f"Extracted numbers: {numbers}")
    # Step 2: Determine operation
    if "more" in question.lower() or "altogether" in question.lower() or "total" in question.lower():
        op = "addition"
        steps.append("Determined operation: addition (more/altogether/total)")
    elif "earn" in question.lower() or "cost" in question.lower() or "price" in question.lower():
        op = "multiplication"
        steps.append("Determined operation: multiplication (earn/cost/price)")
    elif "need" in question.lower() or "left" in question.lower() or "remaining" in question.lower():
        op = "subtraction"
        steps.append("Determined operation: subtraction (need/left/remaining)")
    else:
        op = "unknown"
        steps.append("Operation unknown, defaulting to addition")
    # Step 3: Compute
    if op == "addition" and len(numbers) >= 2:
        result = int(numbers[0]) + int(numbers[1])
    elif op == "multiplication" and len(numbers) >= 2:
        result = int(numbers[0]) * int(numbers[1])
    elif op == "subtraction" and len(numbers) >= 2:
        result = int(numbers[0]) - int(numbers[1])
    else:
        # Fallback: should not happen given our heuristics, but default to 0
        result = 0
    steps.append(f"Computed {op}: {numbers[0]} {op_symbol(op)} {numbers[1]} = {result}")
    steps.append(f"Final answer: {result}")
    # Token estimate: rough count of words in steps
    token_estimate = sum(len(s.split()) for s in steps) + 10  # overhead
    return steps, token_estimate, str(result)

def op_symbol(op: str) -> str:
    return {"addition": "+", "multiplication": "*", "subtraction": "-"}.get(op, "?")

def deep_reasoning_mode(question: str) -> ReasoningTrace:
    """
    Deep reasoning: full CoT + verification (simulate by doing CoT twice and checking agreement).
    """
    steps1, tokens1, ans1 = chain_of_table_reasoning(question)
    steps2, tokens2, ans2 = chain_of_table_reasoning(question)  # second pass
    verified = ans1 == ans2
    steps = ["[Deep Reasoning Mode]"] + steps1
    if verified:
        steps.append("Verification: second pass matched")
    else:
        steps.append(f"Verification mismatch: {ans1} vs {ans2}, taking first")
    return ReasoningTrace(
        mode="DEEP",
        confidence=0.95,  # high after verification
        uncertainty_high=False,
        steps=steps,
        token_estimate=tokens1 + tokens2 + 5,
        final_answer=ans1,
        correct=False,  # will be set later
        notes="Verified chain-of-table"
    )

def chain_of_table_assert_mode(question: str) -> ReasoningTrace:
    """
    Chain-of-Table + $ASSERT validation: produce steps with assertion.
    """
    steps, tokens, ans = chain_of_table_reasoning(question)
    # Add an $ASSERT step
    conf = mock_confidence_heuristic(question)
    assert_step = f'$ASSERT{{condition: "answer {ans} is correct", confidence: {conf}, source: "chain-of-table"}}'
    steps = ["[CoT + $ASSERT Mode]"] + steps + [assert_step]
    return ReasoningTrace(
        mode="COT_ASSERT",
        confidence=conf,
        uncertainty_high=True,
        steps=steps,
        token_estimate=tokens + 5,
        final_answer=ans,
        correct=False,
        notes="Chain-of-table with assertion"
    )

def shortcut_mode(question: str) -> ReasoningTrace:
    """
    Shortcut mode: use heuristics or cached patterns.
    For our mock, we just do a simple keyword-based answer.
    """
    steps = ["[Shortcut Mode]"]
    numbers = re.findall(r'\d+', question)
    if len(numbers) >= 2:
        # Heuristic: if question contains "more" or "altogether", add; if "earn" or "cost", multiply; else subtract
        if "more" in question.lower() or "altogether" in question.lower():
            ans = int(numbers[0]) + int(numbers[1])
            steps.append(f"Heuristic: more/altogether → add {numbers[0]} + {numbers[1]} = {ans}")
        elif "earn" in question.lower() or "cost" in question.lower():
            ans = int(numbers[0]) * int(numbers[1])
            steps.append(f"Heuristic: earn/cost → multiply {numbers[0]} * {numbers[1]} = {ans}")
        elif "need" in question.lower() or "left" in question.lower():
            ans = int(numbers[0]) - int(numbers[1])
            steps.append(f"Heuristic: need/left → subtract {numbers[0]} - {numbers[1]} = {ans}")
        else:
            ans = int(numbers[0]) + int(numbers[1])  # default add
            steps.append(f"Heuristic: default add {numbers[0]} + {numbers[1]} = {ans}")
    else:
        ans = 0
        steps.append("Not enough numbers, guessed 0")
    steps.append(f"Final answer: {ans}")
    token_estimate = sum(len(s.split()) for s in steps) + 5
    return ReasoningTrace(
        mode="SHORTCUT",
        confidence=mock_confidence_heuristic(question),
        uncertainty_high=mock_uncertainty_heuristic(question, mock_confidence_heuristic(question)),
        steps=steps,
        token_estimate=token_estimate,
        final_answer=str(ans),
        correct=False,
        notes="Heuristic-based shortcut"
    )

def unlazy_gates(question: str, threshold: float = 0.8) -> ReasoningTrace:
    """
    Apply Unlazy-Gates pattern with given confidence threshold.
    """
    confidence = mock_confidence_heuristic(question)
    uncertainty_high = mock_uncertainty_heuristic(question, confidence)
    
    if confidence < threshold:
        trace = deep_reasoning_mode(question)
        trace.notes += f" (confidence {confidence} < threshold {threshold})"
    elif uncertainty_high:
        trace = chain_of_table_assert_mode(question)
        trace.notes += f" (confidence {confidence} >= threshold but uncertainty_high)"
    else:
        trace = shortcut_mode(question)
        trace.notes += f" (confidence {confidence} >= threshold and not uncertainty_high)"
    return trace

def evaluate_trace(trace: ReasoningTrace, expected_answer: str) -> ReasoningTrace:
    """Set correctness based on expected answer."""
    trace.correct = (trace.final_answer.strip() == expected_answer.strip())
    return trace

def run_experiment(thresholds: List[float] = [0.5, 0.7, 0.9]) -> Dict[str, Any]:
    """Run experiments with different thresholds and collect results."""
    results = {
        "problems": PROBLEMS,
        "thresholds": thresholds,
        "trials": []
    }
    for thresh in thresholds:
        trial = {
            "threshold": thresh,
            "problem_results": [],
            "summary": {
                "total_correct": 0,
                "total_tokens": 0,
                "mode_counts": {"DEEP": 0, "COT_ASSERT": 0, "SHORTCUT": 0}
            }
        }
        for prob in PROBLEMS:
            trace = unlazy_gates(prob["question"], threshold=thresh)
            trace = evaluate_trace(trace, prob["answer"])
            trial["problem_results"].append({
                "id": prob["id"],
                "question": prob["question"],
                "expected": prob["answer"],
                "mode": trace.mode,
                "confidence": trace.confidence,
                "uncertainty_high": trace.uncertainty_high,
                "steps": trace.steps,
                "token_estimate": trace.token_estimate,
                "final_answer": trace.final_answer,
                "correct": trace.correct,
                "notes": trace.notes
            })
            trial["summary"]["total_correct"] += 1 if trace.correct else 0
            trial["summary"]["total_tokens"] += trace.token_estimate
            trial["summary"]["mode_counts"][trace.mode] += 1
        results["trials"].append(trial)
    return results

def main():
    print("Running Unlazy-Gates Prototype Experiment...")
    results = run_experiment()
    
    # Print summary table
    print("\n=== Summary by Threshold ===")
    print("Threshold | Correct/Total | Avg Tokens | Mode Distribution (DEEP/COT_ASSERT/SHORTCUT)")
    for trial in results["trials"]:
        thresh = trial["threshold"]
        corr = trial["summary"]["total_correct"]
        total = len(PROBLEMS)
        avg_tok = trial["summary"]["total_tokens"] / total
        modes = trial["summary"]["mode_counts"]
        print(f"{thresh:^9} | {corr}/{total:^11} | {avg_tok:^10.1f} | {modes['DEEP']}/{modes['COT_ASSERT']}/{modes['SHORTCUT']}")
    
    # Print detailed trials for inspection
    print("\n=== Detailed Trials ===")
    for trial in results["trials"]:
        print(f"\nThreshold {trial['threshold']}:")
        for pr in trial["problem_results"]:
            print(f"  Problem {pr['id']}:")
            print(f"    Mode: {pr['mode']} (conf={pr['confidence']}, unc_high={pr['uncertainty_high']})")
            print(f"    Answer: {pr['final_answer']} (expected {pr['expected']}) [{'✓' if pr['correct'] else '✗'}]")
            print(f"    Tokens: {pr['token_estimate']}")
            print(f"    Notes: {pr['notes']}")
            # Show first few steps
            if pr['steps']:
                print(f"    Steps: {pr['steps'][0]} ...")
    
    # Save results to file for logging
    output_path = "/run/media/lermf/DADOS_STORAGE/@projetos/Projetos/ist-runtime/examples/unlazy_gates_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")

if __name__ == "__main__":
    main()