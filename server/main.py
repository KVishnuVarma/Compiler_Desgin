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
        "command": ["python"],
    },
    "java": {
        "extension": "java",
        "command": ["javac program.java && java program"],
    },
    "c": {
        "extension": "c",
        "command": ["gcc program.c -o program && ./program"],
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

    run_command = language_info["command"]
    test_results = []

    try:
        # Execute the code for each test case
        for test_case in problem["test_cases"]:
            # Handle shell commands for languages like Java and C
            if isinstance(run_command, list) and len(run_command) > 1:
                command = ' '.join(run_command)  # Concatenate for shell execution
            else:
                command = run_command[0]

            process = subprocess.run(
                command,
                input=test_case["input"] + "\n",  # Pass input to the code
                capture_output=True,
                text=True,
                timeout=10,
                shell=True  # Needed for multi-step commands (Java, C)
            )

            # Capture stdout and compare with expected output
            result = process.stdout.strip()  # User's code output
            expected_result = test_case["expected_output"]  # Expected output
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

        # Return the test results to the frontend
        return {
            "test_results": test_results
        }

    except subprocess.TimeoutExpired:
        return {"error": "Execution timed out"}

    except Exception as e:
        return {"error": f"Unexpected error occurred: {str(e)}"}

    finally:
        # Clean up the generated file after execution
        if os.path.exists(filename):
            os.remove(filename)
