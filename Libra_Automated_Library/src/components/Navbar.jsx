import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import logo from '../assets/logo.svg';

const Navbar = () => {
  const { user, logout, isAdmin, isStudent } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
        <div className="flex justify-between items-center h-16 sm:h-20">
          <div className="flex items-center space-x-3 sm:space-x-4 lg:space-x-8">
            <Link to="/" className="flex items-center space-x-2 sm:space-x-3">
              <img src={logo} alt="Libra Logo" className="h-14 sm:h-20" />
            </Link>
          </div>

          {user && (
            <div className="flex items-center space-x-2 sm:space-x-3 lg:space-x-4">
              <div className="flex items-center space-x-2 sm:space-x-3">
                <div className="text-right hidden md:block">
                  <p className="text-sm font-semibold text-gray-900">{user.first_name} {user.last_name}</p>
                  <p className="text-xs text-gray-500 capitalize">{user.role}</p>
                </div>
                <div className="w-8 h-8 sm:w-9 sm:h-9 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-sm">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 sm:h-5 sm:w-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5.121 17.804A12.083 12.083 0 0112 15c2.49 0 4.786.84 6.879 2.804M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="px-2 sm:px-3 lg:px-4 py-1.5 sm:py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-all duration-200 font-medium text-xs sm:text-sm active:scale-[0.98]"
              >
                <span className="hidden sm:inline">Logout</span>
                <span className="sm:hidden">Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

