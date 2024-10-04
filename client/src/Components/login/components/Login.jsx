// src/Components/login/components/Login.jsx
import React, { useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import AuthContext from "../../context/AuthContext"; // Adjust the path as needed
import authService from "../../services/authService"; // Adjust the path as needed

const Login = () => {
    const navigate = useNavigate();
    const { setUser } = useContext(AuthContext); // This should work now
    const [credentials, setCredentials] = useState({ username: "", password: "" });

    const handleSubmit = async (e) => {
        e.preventDefault();
        const response = await authService.login(credentials);
        if (response.success) {
            setUser(response.data); // Update user context
            navigate("/dashboard"); // Redirect to dashboard
        } else {
            console.error(response.message);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <input 
                type="text" 
                placeholder="Username" 
                value={credentials.username} 
                onChange={(e) => setCredentials({ ...credentials, username: e.target.value })} 
            />
            <input 
                type="password" 
                placeholder="Password" 
                value={credentials.password} 
                onChange={(e) => setCredentials({ ...credentials, password: e.target.value })} 
            />
            <button type="submit">Login</button>
        </form>
    );
};

export default Login;
