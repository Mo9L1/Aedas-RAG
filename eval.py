import json
import sys
sys.path.insert(0, '.')
from answer import AnswerSystem

def evaluate(db_path='vector_db.json'):
    system = AnswerSystem(db_path)

    with open('take_home_dataset/queries.jsonl', 'r') as f:
        queries = [json.loads(line) for line in f]

    results = []
    for item in queries:
        query = item['query']
        user_groups = item['user_groups']
        expected = item['expected_behavior']

        result = system.answer(query, user_groups)

        if expected.startswith('refuse_'):
            expected_reason = expected.replace('refuse_', '')
            actual_refused = result['refusal_reason'] is not None
            correct = actual_refused and expected_reason in (result['refusal_reason'] or '')
        else:
            actual_refused = result['refusal_reason'] is not None
            correct = not actual_refused

        results.append({
            'query': query,
            'expected': expected,
            'actual_refusal': result['refusal_reason'],
            'correct': correct
        })

    correct_count = sum(1 for r in results if r['correct'])
    accuracy = correct_count / len(results)

    print("=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"\nRefusal Accuracy: {correct_count}/{len(results)} = {accuracy:.1%}\n")

    for r in results:
        status = "PASS" if r['correct'] else "FAIL"
        print(f"{status} Query: {r['query'][:50]}...")
        print(f"  Expected: {r['expected']}")
        print(f"  Actual: {'Refused(' + r['actual_refusal'] + ')' if r['actual_refusal'] else 'Answered'}")
        print()

    print("\nMetric: Refusal Accuracy")
    print("- Measures whether the system correctly grants or denies access")
    print("- A refusal is expected when: no_access, expired, or no_evidence")
    print("- Limitation: Does not verify answer quality when access is granted")

    return {'accuracy': accuracy, 'details': results}

if __name__ == "__main__":
    evaluate()
