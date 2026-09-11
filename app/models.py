from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)   # the coding task itself
    function_name = Column(String, nullable=False)
    test_code = Column(Text, nullable=True)   # assert statements to verify correctness
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Solution(Base):
    __tablename__ = "solutions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, nullable=False)   # which task this solution answers
    generated_code = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    solution_id = Column(Integer, nullable=False)
    benchmark_run_id = Column(Integer, nullable=True)
    passed = Column(Integer, nullable=False)      # 1 = pass, 0 = fail
    failure_type = Column(String, nullable=True)   # None if passed
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)   # e.g. "gemini-2.5-flash-run-1"
    created_at = Column(DateTime(timezone=True), server_default=func.now())