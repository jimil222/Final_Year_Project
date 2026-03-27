import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useNotification } from '../hooks/useNotifications';
import BrandLogo from '../components/BrandLogo';
import sideImage from '../assets/side_image.png';

const DEPARTMENTS = [
  'Computer Science',
  'AI & Data Science',
  'Information Technology',
  'Mechanical Engineering',
  'Mathematics',
  'Physics',
  'Chemistry',
  'Other'
];

const Register = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    roll_no: '',
    department: '',
    role: 'student'
  });

  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const { addNotification } = useNotification();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRoleChange = (role) => {
    setFormData({ ...formData, role });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      addNotification('Passwords do not match', 'error');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        roll_no: formData.roll_no,
        role: formData.role,
        department: formData.role === 'student' ? formData.department : undefined
      };

      await register(payload);

      navigate(formData.role === 'admin' ? '/admin' : '/dashboard');
      const roleText = formData.role === 'admin' ? 'Admin' : '';
      addNotification(`Registration successful! Welcome ${roleText}.`, 'success');
    } catch (error) {
      console.error(error);
      addNotification(error.message || 'Registration failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-3 sm:p-6 flex items-center justify-center">
      <div className="w-full max-w-6xl bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-100">
        <div className="grid lg:grid-cols-2">
          <div className="relative hidden lg:block min-h-[760px]">
            <img src={sideImage} alt="Library" className="absolute inset-0 w-full h-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-br from-blue-900/60 to-indigo-900/35" />
            <div className="absolute bottom-10 left-10 right-10 text-white">
              <h2 className="text-3xl font-bold mb-3">Create Your Libra Account</h2>
              <p className="text-blue-100">Register once and unlock smart recommendations, request tracking, and seamless borrowing.</p>
            </div>
          </div>

          <div className="p-4 sm:p-6 lg:p-8 flex items-center">
            <div className="w-full max-w-md mx-auto">
              <div className="lg:hidden mb-5 rounded-xl overflow-hidden relative h-36 sm:h-44">
                <img src={sideImage} alt="Library" className="absolute inset-0 w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-r from-blue-900/55 to-indigo-900/30" />
              </div>

              {/* Header */}
              <div className="text-center mb-4">
                <div className="flex justify-center mb-2">
                  <BrandLogo iconClassName="text-2xl" textClassName="text-3xl" />
                </div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-1">
                  Join the Library
                </h1>
                <p className="text-gray-600 text-xs">
                  Create your account to access resources
                </p>
              </div>

              {/* Role Switcher */}
              <div className="flex space-x-1 mb-4 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => handleRoleChange('student')}
            type="button"
            className={`flex-1 py-2 rounded-md font-semibold text-sm transition-all ${
              formData.role === 'student'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Student
          </button>
          <button
            onClick={() => handleRoleChange('admin')}
            type="button"
            className={`flex-1 py-2 rounded-md font-semibold text-sm transition-all ${
              formData.role === 'admin'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Admin
          </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-3">

          {/* Full Name */}
          <div>
            <label className="block text-gray-700 text-sm font-semibold mb-1">
              Full Name
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="input-modern"
              placeholder="Ex: John Doe"
            />
          </div>

          {/* Roll Number & Department */}
          <div className={`grid grid-cols-1 ${formData.role === 'student' ? 'md:grid-cols-2' : ''} gap-3`}>
            <div>
              <label className="block text-gray-700 text-sm font-semibold mb-1">
                {formData.role === 'admin' ? 'Admin ID / Employee ID' : 'Roll Number'}
              </label>
              <input
                type="text"
                name="roll_no"
                value={formData.roll_no}
                onChange={handleChange}
                required
                className="input-modern"
                placeholder={formData.role === 'admin' ? 'Ex: ADM001' : 'Ex: 22CS101'}
              />
            </div>

            {formData.role === 'student' && (
              <div>
                <label className="block text-gray-700 text-sm font-semibold mb-1">
                  Department
                </label>
                <select
                  name="department"
                  value={formData.department}
                  onChange={handleChange}
                  required
                  className="input-modern"
                >
                  <option value="">Select Dept</option>
                  {DEPARTMENTS.map((dept) => (
                    <option key={dept} value={dept}>
                      {dept}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Email */}
          <div>
            <label className="block text-gray-700 text-sm font-semibold mb-1">
              Email Address
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="input-modern"
              placeholder="student@college.edu"
            />
          </div>

          {/* Passwords */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-gray-700 text-sm font-semibold mb-1">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                className="input-modern"
                placeholder="Min 6 chars"
              />
            </div>
            <div>
              <label className="block text-gray-700 text-sm font-semibold mb-1">
                Confirm
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                className="input-modern"
                placeholder="Confirm password"
              />
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full text-sm mt-1"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Creating Account...
              </span>
            ) : (
              'Register'
            )}
          </button>
              </form>

              {/* Footer */}
              <p className="mt-4 text-center text-gray-600 text-sm">
                Already have an account?{' '}
                <Link to="/login" className="text-blue-600 hover:text-blue-700 font-semibold">
                  Sign In
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
