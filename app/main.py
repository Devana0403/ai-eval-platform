from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app import models, schemas

from app.llm import generate_solution, generate_test_code
from app.grader import grade_solution
from app.benchmark import run_benchmark
from app.test_builder import build_test_code_from_examples

from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def root():
    return {"status": "AI Eval Platform is running"}

@app.post("/tasks", response_model=schemas.TaskResponse)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    final_test_code = task.test_code

    if not final_test_code and task.examples:
        if not task.function_name:
            raise HTTPException(status_code=400, detail="function_name is required when using examples")
        final_test_code = build_test_code_from_examples(task.function_name, task.examples)

    elif not final_test_code and task.auto_generate_tests:
        if not task.function_name:
            raise HTTPException(status_code=400, detail="function_name is required for auto-generated tests")
        raw = generate_test_code(task.description, task.function_name)
        final_test_code = raw.strip().removeprefix("```python").removeprefix("```").removesuffix("```").strip()

    new_task = models.Task(
        description=task.description,
        function_name=task.function_name,
        test_code=final_test_code
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.get("/tasks", response_model=list[schemas.TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    print("Inside list_tasks endpoint")
    return db.query(models.Task).all()

@app.get("/tasks/search", response_model=list[schemas.TaskResponse])
def search_tasks(q: str, db: Session = Depends(get_db)):
    return db.query(models.Task).filter(models.Task.description.ilike(f"%{q}%")).all()

@app.patch("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, update: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")

    task.test_code = update.test_code
    db.commit()
    db.refresh(task)
    return task

@app.post("/tasks/{task_id}/generate", response_model=schemas.SolutionResponse)
def generate_for_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")

    # raw_code = generate_solution(task.description)
    raw_code = generate_solution(task.description, task.function_name)
    cleaned_code = raw_code.strip().removeprefix("```python").removeprefix("```").removesuffix("```").strip()

    new_solution = models.Solution(task_id=task_id, generated_code=cleaned_code)
    db.add(new_solution)
    db.commit()
    db.refresh(new_solution)
    return new_solution


@app.post("/solutions/{solution_id}/evaluate", response_model=schemas.EvaluationResponse)
def evaluate_solution(solution_id: int, expected_task_id: int | None = None, db: Session = Depends(get_db)):
    solution = db.query(models.Solution).filter(models.Solution.id == solution_id).first()
    if not solution:
        raise HTTPException(status_code=404, detail=f"Solution with id {solution_id} not found")

    # Optional safety check: catches human/client mix-ups like using the wrong id
    if expected_task_id is not None and solution.task_id != expected_task_id:
        raise HTTPException(
            status_code=400,
            detail=f"Solution {solution_id} belongs to task {solution.task_id}, not task {expected_task_id}"
        )

    task = db.query(models.Task).filter(models.Task.id == solution.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with id {solution.task_id} not found for this solution")
    if not task.test_code:
        raise HTTPException(status_code=400, detail=f"Task {task.id} has no test_code to grade against")

    result = grade_solution(solution.generated_code, task.test_code)
    new_eval = models.Evaluation(
        solution_id=solution_id,
        passed=1 if result["passed"] else 0,
        failure_type=result["failure_type"],
        stdout=result["stdout"],
        stderr=result["stderr"]
    )
    db.add(new_eval)
    db.commit()
    db.refresh(new_eval)
    new_eval.passed = bool(new_eval.passed)
    return new_eval


@app.post("/benchmarks/run", response_model=schemas.BenchmarkSummary)
def run_new_benchmark(label: str, db: Session = Depends(get_db)):
    return run_benchmark(db, label)


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],       # fine for local dev; we'll lock this down before deploying
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://victorious-glacier-079dc1610.3.azurestaticapps.net"],
    allow_methods=["*"],
    allow_headers=["*"],
)