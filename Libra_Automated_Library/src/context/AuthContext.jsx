import { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, register as apiRegister, verifyToken } from '../utils/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    // Avoid crash if used outside provider (e.g. after error boundary remount)
    return {
      user: null,
      token: null,
      loading: false,
      login: async () => {},
      register: async () => {},
      logout: () => {},
      isAdmin: false,
      isStudent: false,
    };
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedToken = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');

        if (storedToken && storedUser) {
          // Validate user data before using it
          const parsedUser = JSON.parse(storedUser);
          if (parsedUser && parsedUser.id && parsedUser.role) {
            // Restore session from storage. We keep the session until user explicitly logs out.
            setUser(parsedUser);
            setToken(storedToken);

            // Optionally verify token in background, but do NOT auto-logout on failure.
            try {
              const freshUser = await verifyToken(storedToken);
              if (freshUser) {
                setUser(freshUser);
                localStorage.setItem('user', JSON.stringify(freshUser));
              }
            } catch (error) {
              console.warn('Token verification failed, keeping stored session until logout.', error);
            }
          } else {
            // Invalid user data found, clear it
            console.warn('Invalid user data found in storage, clearing...');
            localStorage.removeItem('user');
            localStorage.removeItem('token');
          }
        }
      } catch (error) {
        console.error('Error during auth initialization:', error);
        // Clear storage on any error to prevent infinite loops
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email, password, role) => {
    try {
      const response = await apiLogin(email, password, role);
      setUser(response.user);
      setToken(response.token);
      localStorage.setItem('user', JSON.stringify(response.user));
      localStorage.setItem('token', response.token);
      return response;
    } catch (error) {
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      const response = await apiRegister(userData);
      setUser(response.user);
      setToken(response.token);
      localStorage.setItem('user', JSON.stringify(response.user));
      localStorage.setItem('token', response.token);
      return response;
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  };

  const isAdmin = user?.role === 'admin';
  const isStudent = user?.role === 'student';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        register,
        logout,
        isAdmin,
        isStudent,
        loading
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

