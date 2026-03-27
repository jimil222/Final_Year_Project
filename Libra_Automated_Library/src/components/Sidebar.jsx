import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Book, BookOpen, Settings, Menu, X, FileText, Plus, Activity, Radio } from 'lucide-react';

const Sidebar = () => {
  const { isAdmin, isStudent } = useAuth();
  const location = useLocation();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const studentLinks = [
    { path: '/dashboard', label: 'Dashboard', icon: Book }
  ];

  const adminLinks = [
    { path: '/admin', label: 'Admin Panel', icon: Settings }
  ];

  const links = isAdmin ? adminLinks : isStudent ? studentLinks : [];
  const isAdminRoute = isAdmin && location.pathname === '/admin';
  const isStudentRoute = isStudent && location.pathname === '/dashboard';
  const currentTab = new URLSearchParams(location.search).get('tab');
  const currentAdminTab = currentTab || 'requests';
  const currentStudentTab = currentTab || 'browse';

  const studentSectionLinks = [
    { tab: 'browse', label: 'Browse Library', icon: BookOpen },
    { tab: 'history', label: 'Request History', icon: FileText }
  ];

  const adminSectionLinks = [
    { tab: 'requests', label: 'Pending Requests', icon: FileText },
    { tab: 'inventory', label: 'Book Inventory', icon: BookOpen },
    { tab: 'scan-inventory', label: 'Scan Inventory', icon: Radio },
    { tab: 'add-book', label: 'Add New Book', icon: Plus },
  ];

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="lg:hidden fixed top-16 sm:top-20 left-3 sm:left-4 z-40 p-2 bg-white rounded-lg shadow-md border border-gray-200 hover:bg-gray-50 transition-colors"
        aria-label="Toggle menu"
      >
        {isMobileOpen ? <X className="w-5 h-5 text-gray-700" /> : <Menu className="w-5 h-5 text-gray-700" />}
      </button>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:fixed top-16 sm:top-20 left-0 z-30 w-[85vw] max-w-xs sm:w-72 lg:w-64 bg-white border-r border-gray-200 h-[calc(100vh-4rem)] sm:h-[calc(100vh-5rem)] overflow-y-auto p-4 transform transition-transform duration-300 ease-in-out ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          }`}
      >
        <nav className="space-y-1">
          {links.map((link) => {
            const Icon = link.icon;
            return (
              <NavLink
                key={link.path}
                to={link.path}
                onClick={() => setIsMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${isActive
                    ? 'bg-blue-50 text-blue-700 font-semibold border-l-4 border-blue-600'
                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900 font-medium'
                  }`
                }
              >
                <Icon className="text-xl flex-shrink-0" />
                <span>{link.label}</span>
              </NavLink>
            );
          })}

          {isStudentRoute && (
            <div className="pt-6 mt-6 border-t border-gray-200 space-y-1">
              {studentSectionLinks.map((link) => {
                const Icon = link.icon;
                const isActive = currentStudentTab === link.tab;

                return (
                  <NavLink
                    key={link.tab}
                    to={`/dashboard?tab=${link.tab}`}
                    onClick={() => setIsMobileOpen(false)}
                    className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                      isActive
                        ? 'bg-blue-600 text-white font-semibold shadow-md'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900 font-medium'
                    }`}
                  >
                    <Icon className="text-xl flex-shrink-0" />
                    <span>{link.label}</span>
                  </NavLink>
                );
              })}
            </div>
          )}

          {isAdminRoute && (
            <div className="pt-6 mt-6 border-t border-gray-200 space-y-1">
              {adminSectionLinks.map((link) => {
                const Icon = link.icon;
                const isActive = currentAdminTab === link.tab;

                return (
                  <NavLink
                    key={link.tab}
                    to={`/admin?tab=${link.tab}`}
                    onClick={() => setIsMobileOpen(false)}
                    className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                      isActive
                        ? 'bg-blue-600 text-white font-semibold shadow-md'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900 font-medium'
                    }`}
                  >
                    <Icon className="text-xl flex-shrink-0" />
                    <span>{link.label}</span>
                  </NavLink>
                );
              })}
            </div>
          )}
        </nav>
      </aside>
    </>
  );
};

export default Sidebar;

