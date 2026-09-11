from pydantic import BaseModel
from datetime import datetime

class Example(BaseModel):
    inputs: list          # positional arguments, e.g. [2, 3]
    expected_output: object

class TaskCreate(BaseModel):
    description: str
    function_name: str
    test_code: str | None = None
    examples: list[Example] | None = None
    auto_generate_tests: bool = False

class TaskResponse(BaseModel):
    id: int
    description: str
    function_name: str
    test_code: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class TaskUpdate(BaseModel):
    test_code: str | None = None

class SolutionResponse(BaseModel):
    id: int
    task_id: int
    generated_code: str
    created_at: datetime

    class Config:
        from_attributes = True

class EvaluationResponse(BaseModel):
    id: int
    solution_id: int
    passed: bool
    failure_type: str | None
    stdout: str
    stderr: str
    created_at: datetime

    class Config:
        from_attributes = True

class BenchmarkResult(BaseModel):
    task_id: int
    passed: bool
    failure_type: str | None

class BenchmarkSummary(BaseModel):
    benchmark_run_id: int
    label: str
    total_tasks: int
    passed: int
    pass_rate: float
    failure_breakdown: dict[str, int]
    results: list[BenchmarkResult]
