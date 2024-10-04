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
        "command": ["python", "program.py"],  # Adjust this to match your Python path if needed
    },
    "java": {
        "extension": "java",
        "command": ["javac program.java && java program"],
    },
    "c": {
        "extension": "c",
        "command": ["gcc program.c -o program.exe && ./program.exe"],
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
        # Execute the code for each test case
        for test_case in problem["test_cases"]:
            input_data = test_case["input"] + "\n"  # Prepare input data
            expected_result = test_case["expected_output"]  # Expected output

            # Define the run command based on the language
            if code_input.language == "python":
                run_command = ["python", filename]  # For Python

            elif code_input.language == "c":
                # Compile C code first
                compile_command = ["gcc", filename, "-o", "program.exe"]
                compile_process = subprocess.run(compile_command, capture_output=True, text=True, shell=True)

                # Check if compilation was successful
                if compile_process.returncode != 0:
                    test_results.append({
                        "input": test_case["input"],
                        "expected_output": expected_result,
                        "user_output": "Compilation Error",
                        "test_passed": False,
                        "error": compile_process.stderr.strip()
                    })
                    continue  # Skip further execution if compilation fails

                run_command = ["./program.exe"]  # For C

            elif code_input.language == "java":
                # Compile Java code first
                compile_command = ["javac", filename]
                compile_process = subprocess.run(compile_command, capture_output=True, text=True, shell=True)

                # Check if compilation was successful
                if compile_process.returncode != 0:
                    test_results.append({
                        "input": test_case["input"],
                        "expected_output": expected_result,
                        "user_output": "Compilation Error",
                        "test_passed": False,
                        "error": compile_process.stderr.strip()
                    })
                    continue  # Skip further execution if compilation fails

                run_command = ["java", "program"]  # For Java

            # Run the code
            try:
                process = subprocess.run(
                    run_command,
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=10,  # Limit execution time
                    shell=True
                )

                if process.returncode != 0:
                    # Capture any runtime errors
                    error_message = process.stderr.strip()
                    test_results.append({
                        "input": test_case["input"],
                        "expected_output": expected_result,
                        "user_output": "Runtime Error",
                        "test_passed": False,
                        "error": error_message
                    })
                else:
                    # Capture stdout and compare with expected output
                    result = process.stdout.strip()
                    test_passed = result == expected_result

                    # Append result for this test case to the results list
                    test_results.append({
                        "input": test_case["input"],
                        "expected_output": expected_result,
                        "user_output": result,
                        "test_passed": test_passed,
                        "error": ""
                    })

            except subprocess.TimeoutExpired:
                test_results.append({
                    "input": test_case["input"],
                    "expected_output": expected_result,
                    "user_output": "Timeout",
                    "test_passed": False,
                    "error": "Execution timed out"
                })

    except Exception as e:
        return {"error": f"Unexpected error occurred: {str(e)}"}

    finally:
        # Clean up the generated files after execution
        if os.path.exists(filename):
            os.remove(filename)
        if code_input.language == "c" and os.path.exists("program.exe"):
            os.remove("program.exe")
        if code_input.language == "java" and os.path.exists("program.class"):
            os.remove("program.class")

    # Return the test results to the frontend
    return {"test_results": test_results}
