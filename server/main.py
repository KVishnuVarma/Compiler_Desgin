from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pymongo import MongoClient
from bson.objectid import ObjectId
import subprocess

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MongoClient("mongodb://localhost:27017")
db = client["mnc"] 
questions_collection = db["questions"]


class CodeInput(BaseModel):
    language: str
    code: str
    input_data: Optional[str] = ""


SUPPORTED_LANGUAGES = {
    "python": {
        "extension": "py",
        "run_command": ["python", "program.py"],
    },
    "java": {
        "extension": "java",
        "compile_command": ["javac", "program.java"],
        "run_command": ["java", "program"],
    },
    "c": {
        "extension": "c",
        "compile_command": ["gcc", "program.c", "-o", "program.exe"],
        "run_command": ["./program.exe"],
    },
}


def get_test_cases_from_db(question_id):
    question = questions_collection.find_one({"_id": ObjectId(question_id)})
    if not question or "testCases" not in question:
        raise HTTPException(status_code=404, detail="Question or test cases not found")
    return question["testCases"]


def execute_code(language: str, code: str, input_data: str):
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="Unsupported language")

    language_config = SUPPORTED_LANGUAGES[language]
    extension = language_config["extension"]
    source_file = f"program.{extension}"


    with open(source_file, "w") as f:
        f.write(code)


    if "compile_command" in language_config:
        compile_process = subprocess.run(language_config["compile_command"], capture_output=True, text=True)
        if compile_process.returncode != 0:
            return {"error": compile_process.stderr.strip()}


    process = subprocess.run(
        language_config["run_command"],
        input=input_data,
        capture_output=True,
        text=True
    )

    # Return output or error
    if process.returncode == 0:
        return {"output": process.stdout.strip()}
    else:
        return {"error": process.stderr.strip()}

@app.post("/execute/")
async def execute_code_endpoint(code_input: CodeInput, question_id: str = Body(...)):
    try:
        test_cases = get_test_cases_from_db(question_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    results = []
    for test_case in test_cases:
        input_data = test_case["input"]
        expected_output = test_case["expected_output"]

        result = execute_code(code_input.language, code_input.code, input_data)

        test_passed = result.get("output") == expected_output
        results.append({
            "input": input_data,
            "expected_output": expected_output,
            "user_output": result.get("output"),
            "test_passed": test_passed,
            "error": result.get("error"),
        })

    return {"test_results": results}
