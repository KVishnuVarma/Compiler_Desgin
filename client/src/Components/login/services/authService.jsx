const API_URL = 'http://localhost:5000/api/auth';

const login = async (Credential) => {
    const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'applicaton/json',
        },
        body: JSON.stringify(Credentials),
    });

    if (response.ok) {
        const data = await response.json();
        localStorage.setItem('user',JSON.stringify(data));
        return data;
    }
    else {
        throw new Error('Login failed');
    }
};

const signup = async (userDetails) => {
    const response = await fetch(`${API_URL}/signup`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        throw new Error('Signup failed');
    }
};

const authService = { login, signup};
export default authService;