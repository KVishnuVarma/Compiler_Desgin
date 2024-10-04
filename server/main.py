from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Update with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB client setup (replace with your credentials)
client = MongoClient('mongodb://localhost:27017/')
db = client["code_database"]
collection = db["test_results"]

# Define a model for input
class CodeInput(BaseModel):
    language: str
    code: str
    input_data: str = ""

# Supported languages with commands
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
        "run_command": ["program.exe"],
    },
}

# Problem and multiple test cases
problem = {
    "title": "Sum of Two Numbers",
    "description": "Write a program that takes two integers and returns their sum.",
    "test_cases": [
        {"input": "3 5", "expected_output": "8"},
        {"input": "-2 4", "expected_output": "2"},
        {"input": "0 0", "expected_output": "0"},
        {"input": "1000000 9999999", "expected_output": "10999999"},
        {"input": "-7 -8", "expected_output": "-15"},
    ]
}

@app.post("/execute/")
async def execute_code(code_input: CodeInput):
    # Check if language is supported
    if code_input.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="Language not supported")

    language_info = SUPPORTED_LANGUAGES[code_input.language]
    filename = f"program.{language_info['extension']}"

    # Write the user's code to a file
    with open(filename, "w") as f:
        f.write(code_input.code)

    test_results = []

    try:
        # For compiled languages, compile the code first
        if code_input.language in ["java", "c"]:
            compile_command = language_info.get("compile_command")
            compile_process = subprocess.run(
                compile_command,
                capture_output=True,
                text=True
            )
            if compile_process.returncode != 0:
                # Compilation failed
                return {"error": compile_process.stderr.strip()}

        # Execute the code for each test case
        for test_case in problem["test_cases"]:
            input_data = test_case["input"] + "\n"  # Prepare input data
            expected_result = test_case["expected_output"]  # Expected output

            if code_input.language == "python":
                run_command = ["python", filename]
            else:
                run_command = language_info.get("run_command")

            try:
                process = subprocess.run(
                    run_command,
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=10,  # Limit execution time
                    shell=False  # Use shell=False for security
                )


                if process.returncode !=0:
                    return {"error":process.stderr.strip()}
                
                result = process.stdout.strip()

                if result == "":
                    result = "No output returned from the execution"
                test_passed = result == expected_result

                # Append result for this test case to the results list
                test_results.append({
                    "input": test_case["input"],
                    "expected_output": expected_result,
                    "user_output": result,
                    "test_passed": test_passed,
                    "error": process.stderr.strip() if process.returncode != 0 else ""
                })

                # Save result to MongoDB (optional)
                result_entry = {
                    "problem": problem["title"],
                    "user_code": code_input.code,
                    "user_input": test_case["input"],
                    "expected_output": expected_result,
                    "user_output": result,
                    "test_passed": test_passed,
                }
                collection.insert_one(result_entry)

            except subprocess.TimeoutExpired:
                test_results.append({
                    "input": test_case["input"],
                    "expected_output": expected_result, 
                    "user_output": "",
                    "test_passed": False,
                    "error": "Execution timed out"
                })

            except Exception as e:
                test_results.append({
                    "input": test_case["input"],
                    "expected_output": expected_result,
                    "user_output": "",
                    "test_passed": False,
                    "error": f"Unexpected error occurred: {str(e)}"
                })

        # Return the test results to the frontend
        return {
            "test_results": test_results
        }

    finally:
        # Clean up the generated files after execution
        if os.path.exists(filename):
            os.remove(filename)
        if code_input.language == "c":
            if os.path.exists("program.exe"):
                os.remove("program.exe")
        if code_input.language == "java":
            if os.path.exists("program.class"):
                os.remove("program.class")
