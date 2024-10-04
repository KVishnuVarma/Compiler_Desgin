import React, { useState, useEffect } from "react";
import MonacoEditor from "@monaco-editor/react";
import "./compiler.css"

function EditorComponent() {
  const [code, setCode] = useState("// write your code here");
  const [output, setOutput] = useState([]);
  const [showCongrats, setShowCongrats] = useState(false); // State to show congrats message after all test cases pass
  const [showSampleTest, setShowSampleTest] = useState(true); // New state to control when to show sample test case
  const [compilerError, setCompilerError] = useState(null); // New state to show compiler error
  const [timer, setTimer] = useState(0); // State to manage the countdown timer
  const [isTimerRunning, setIsTimerRunning] = useState(false); // State to control when the timer is running
  const [language, setLanguage] = useState("python"); // State to manage selected language

  // Example problem with input validation
  const problem = {
    title: "Sum of Two Numbers",
    description:
      "Write a program that takes two integers as input and returns their sum.",
    inputFormat: "Two space-separated integers",
    sampleInput: "1 2",
    expectedOutput: "3", // Expected output for sample test case
  };

  // Function to format the timer as hours:minutes:seconds
  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs}h : ${mins}m : ${secs}s`;
  };

  // useEffect hook to manage the timer countdown
  useEffect(() => {
    let timerInterval = null;
    if (isTimerRunning && timer > 0) {
      timerInterval = setInterval(() => {
        setTimer((prevTime) => prevTime - 1);
      }, 1000);
    } else if (timer === 0) {
      setIsTimerRunning(false);
    }
    return () => clearInterval(timerInterval); // Cleanup the interval
  }, [isTimerRunning, timer]);

  // Function to handle the start of the timer when "Run Code" or "Submit Code" is clicked
  const startTimer = () => {
    setTimer(3600); // Set the timer for 1 hour (3600 seconds)
    setIsTimerRunning(true);
  };

  // Function to execute code and show only the first test case result
  const handleRun = async () => {
    startTimer(); // Start the timer when running code
    try {
      setShowSampleTest(false); // Hide the sample test output initially
      setCompilerError(null); // Reset the compiler error
      const response = await fetch("http://127.0.0.1:8000/execute/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          code,
          language, // Passing languaged language
          input_data: problem.sampleInput, // Only passing the sample input for a single test case
        }),
      });
      const data = await response.json();

      if (data.test_results && data.test_results.length > 0) {
        // Get only the first test case result
        const firstTestResult = data.test_results[0];

        if (firstTestResult.test_passed) {
          setShowSampleTest(true); // Show the sample test case output if it passes
        } else {
          // Show compiler error if the first test case fails
          setCompilerError("Sample test case failed! Check your logic.");
        }

        // Show only the first test case result
        setOutput([firstTestResult]); // Display only the first test case in the output
      } else {
        setOutput([{ error: "No output returned from the execution." }]);
      }
    } catch (error) {
      setOutput([{ error: `Error executing code: ${error.message}` }]);
    }
  };

  // Function to execute and validate against all predefined test cases
  const handleSubmit = async () => {
    startTimer(); // Start the timer when submitting code
    try {
      const response = await fetch("http://127.0.0.1:8000/execute/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code, language, input_data: "" }), // Backend will run its own test cases
      });
      const data = await response.json();
      if (data.test_results) {
        // Set all test results from the backend
        setOutput(data.test_results);

        // Check if all tests passed and show congrats message
        const allTestsPassed = data.test_results.every(
          (test) => test.test_passed
        );
        setShowCongrats(allTestsPassed);

        // Set error message if not all tests pass
        if (!allTestsPassed) {
          setCompilerError("One or more test cases failed.");
        } else {
          setCompilerError(null); // Reset compiler error if everything passed
        }
      } else {
        setOutput([{ error: "No test results returned from the execution." }]);
      }
    } catch (error) {
      setOutput([{ error: `Error executing code: ${error.message}` }]);
    }
  };

  return (
    <div className="container">
      {/* Header Section */}
      <header className="header">
        <h1>Free Code</h1>
      </header>

      {/* Main Content: split the screen */}
      <div className="main-content">
        {/* Left Panel: Problem Description */}
        <div className="left-panel">
          <h2>{problem.title}</h2>
          <p>{problem.description}</p>
          <p>
            <strong>Input Format:</strong> {problem.inputFormat}
          </p>
          <p>
            <strong>Sample Input:</strong> {problem.sampleInput}
          </p>
          <p>
            <strong>Expected Output:</strong> {problem.expectedOutput}
          </p>
        </div>

        {/* Right Panel: Monaco Editor */}
        <div className="right-panel">
          {/* Language Selection Dropdown */}
          <div className="language-selection">
            <label htmlFor="language">Select Language: </label>
            <select
              id="language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="python">Python</option>
              <option value="java">Java</option>
              <option value="c">C</option>
            </select>
          </div>

          <MonacoEditor
            height="400px"
            width="100%"
            language={language} // Use the selected language
            theme="vs-dark"
            value={code}
            onChange={(newValue) => setCode(newValue || code)}
          />

          {/* Timer Display */}
          <div className="timer">
            <h3>{formatTime(timer)}</h3> {/* Using formatTime to display hours, minutes, and seconds */}
          </div>

          {/* Submit and Run Buttons */}
          <div className="btn-div">
            {/* Run Button */}
            <button className="run-btn" onClick={handleRun}>
              Run Code
            </button>

            {/* Submit Button */}
            <button className="submit-btn" onClick={handleSubmit}>
              Submit Code
            </button>
          </div>

          {/* Congrats Message Section */}
          {showCongrats && (
            <div className="congrats">
              <h2>Congratulations! All Test Cases Passed!</h2>
            </div>
          )}

          {/* Conditionally render the sample test case result when the Run button is clicked and if the test passes */}
          {showSampleTest && (
            <div className="sample">
              <h3>Sample Test Case</h3>
            </div>
          )}

          {/* Display compiler error if the first test case fails */}
          {compilerError && (
            <div className="error">
              <h3>{compilerError}</h3>
            </div>
          )}

          {/* Output Section (appears after clicking Run/Submit) */}
          <div className="output-section">
            <h3>Output:</h3>
            {output.length > 0 ? (
              output.map((result, index) => (
                <div
                  key={index}
                  className={`output-result ${
                    result.test_passed ? "pass" : "fail"
                  }`}
                >
                  <p>
                    <strong>Test Case {index + 1}:</strong>
                  </p>
                  <p>
                    <strong>Input:</strong>{" "}
                    {result.input || problem.sampleInput}
                  </p>
                  <p>
                    <strong>Expected Output:</strong>{" "}
                    {result.expected_output || "N/A"}
                  </p>
                  <p>
                    <strong>User Output:</strong>{" "}
                    {result.user_output || "Error"}
                  </p>
                  {result.error && (
                    <p className="error-msg">
                      <strong>Error:</strong> {result.error}
                    </p>
                  )}
                  <p>
                    <strong>Result:</strong>{" "}
                    {result.test_passed ? "Passed" : "Failed"}
                  </p>
                </div>
              )) 
            ) : (
              <p>No output available yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default EditorComponent;
