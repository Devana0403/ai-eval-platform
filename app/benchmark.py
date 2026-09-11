from collections import Counter
from sqlalchemy.orm import Session
from app import models
from app.llm import generate_solution
from app.grader import grade_solution

def run_benchmark(db: Session, label: str) -> dict:
    tasks = db.query(models.Task).filter(models.Task.test_code.isnot(None)).all()

    benchmark_run = models.BenchmarkRun(label=label)
    db.add(benchmark_run)
    db.commit()
    db.refresh(benchmark_run)

    results = []
    failure_counts = Counter()
    passed_count = 0

    for task in tasks:
        # raw_code = generate_solution(task.description)
        raw_code = generate_solution(task.description, task.function_name)
        cleaned_code = raw_code.strip().removeprefix("```python").removeprefix("```").removesuffix("```").strip()

        solution = models.Solution(task_id=task.id, generated_code=cleaned_code)
        db.add(solution)
        db.commit()
        db.refresh(solution)

        grade_result = grade_solution(cleaned_code, task.test_code)

        evaluation = models.Evaluation(
            solution_id=solution.id,
            benchmark_run_id=benchmark_run.id,
            passed=1 if grade_result["passed"] else 0,
            failure_type=grade_result["failure_type"],
            stdout=grade_result["stdout"],
            stderr=grade_result["stderr"]
        )
        db.add(evaluation)
        db.commit()

        if grade_result["passed"]:
            passed_count += 1
        else:
            failure_counts[grade_result["failure_type"]] += 1

        results.append({
            "task_id": task.id,
            "passed": grade_result["passed"],
            "failure_type": grade_result["failure_type"]
        })

    total = len(tasks)
    return {
        "benchmark_run_id": benchmark_run.id,
        "label": label,
        "total_tasks": total,
        "passed": passed_count,
        "pass_rate": round(passed_count / total, 3) if total > 0 else 0,
        "failure_breakdown": dict(failure_counts),
        "results": results
    }