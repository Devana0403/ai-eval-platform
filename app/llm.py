## Not just writing in main so that if I want to change models later then it won't be as much of a hassle

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

def generate_solution(task_description: str, function_name: str) -> str:
    prompt = (
        f"Write a Python function named exactly '{function_name}' that does the following: "
        f"{task_description}\n\n"
        f"Only output the code, no explanation, no markdown formatting."
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(URL, json=payload)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

def generate_test_code(description: str, function_name: str) -> str:
    prompt = (
        f"Write simple Python assert-based test cases for a function called "
        f"'{function_name}' that does the following: {description}\n\n"
        f"Only output valid Python code with assert statements, no explanations, "
        f"no markdown formatting. Include a final print('All tests passed') line "
        f"only if all asserts are reached."
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(URL, json=payload)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]