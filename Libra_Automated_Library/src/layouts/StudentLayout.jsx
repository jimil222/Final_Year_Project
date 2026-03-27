import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';

const StudentLayout = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="flex relative">
        <Sidebar />
        <main className="flex-1 w-full p-3 sm:p-4 md:p-6 lg:p-8 lg:ml-64">
          {children}
        </main>
      </div>
    </div>
  );
};

export default StudentLayout;

