  import React, { useState } from 'react';
  import MonacoEditor from '@monaco-editor/react';

  function EditorComponent() {
    const [code, setCode] = useState('// Start coding here');
    const [output, setOutput] = useState(''); // For displaying the output in the UI

    function handleExecute() {
      fetch('http://127.0.0.1:8000/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }), // Send the code as JSON in the request body
      })
        .then(response => response.json())
        .then(data => {
          setOutput(data.result); // Set the output to display in the UI
        })
        .catch(error => {
          setOutput('Error executing code: ' + error.message); // Display error in case of failure
        });
    }

    return (
      <div>
        <MonacoEditor
          height="5000px"
          language="javascript"
          value={code}
          onChange={(newValue) => setCode(newValue)}
        />
        <button onClick={handleExecute}>Run Code</button>

        {/* Output Section */}
        <div>
          <h3>Output:</h3>
          <pre>{output}</pre> {/* Displaying output in the frontend */}
        </div>
      </div>
    );
  }

  export default EditorComponent;
