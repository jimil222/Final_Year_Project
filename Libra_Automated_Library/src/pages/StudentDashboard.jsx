import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useBookContext } from '../context/BookContext';
import { useBookActions } from '../hooks/useBookActions';
import { formatDate } from '../utils/helpers';
import SearchBar from '../components/SearchBar';
import BookCard from '../components/BookCard';
import RequestCard from '../components/RequestCard';
import { Book, ClipboardList, Star, Hand, TrendingUp, BookOpen } from 'lucide-react';
import RecommendationModal from '../components/RecommendationModal';
import libraryImage from '../assets/Library.png';

const StudentDashboard = () => {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const activeTab = new URLSearchParams(location.search).get('tab') || 'browse';
  const {
    books,
    requests,
    recommendations,
    loadBooks,
    loadRequests,
    loadRecommendations,
    loading: booksLoading
  } = useBookContext();

  const { requestBook, loading: actionLoading } = useBookActions();
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredBooks, setFilteredBooks] = useState([]);

  // Modal State
  const [showRecModal, setShowRecModal] = useState(false);
  const [lastRequestedBook, setLastRequestedBook] = useState('');
  const [lastRequestedBookDept, setLastRequestedBookDept] = useState('');

  // ==============================
  // INITIAL LOAD
  // ==============================
  useEffect(() => {
    loadBooks();

    if (user?.id) {
      loadRequests(user.id);
      loadRecommendations();
    }
  }, [user?.id]);

  // ==============================
  // AUTO REFRESH (Polling)
  // ==============================
  useEffect(() => {
    if (!user?.id) return;

    const interval = setInterval(() => {
      loadBooks();
      loadRequests(user.id);
      loadRecommendations();
    }, 4000); // 4 seconds

    return () => clearInterval(interval);
  }, [user?.id]);

  // ==============================
  // SEARCH FILTER
  // ==============================
  useEffect(() => {
    const availableBooks = books.filter(
      book => book.status === 'available'
    );

    if (searchQuery) {
      const filtered = availableBooks.filter(
        book =>
          book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          book.author.toLowerCase().includes(searchQuery.toLowerCase()) ||
          book.book_id.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredBooks(filtered);
    } else {
      setFilteredBooks(availableBooks);
    }
  }, [searchQuery, books]);

  if (booksLoading && books.length === 0) {
    return (
      <div className="text-center text-gray-500 py-12">
        Loading books...
      </div>
    );
  }

  const handleRequest = async (bookId, bookTitle, bookDept) => {
    if (user?.id) {
      await requestBook(user, bookId);

      setLastRequestedBook(bookTitle);
      setLastRequestedBookDept(bookDept);
      setShowRecModal(true);

      // Immediate refresh after request
      loadRequests(user.id);
      loadBooks();
      loadRecommendations();
    }
  };

  const myRequests = requests.filter(
    req => String(req.user_id) === String(user?.id)
  );
  const availableBooksCount = books.filter((book) => book.status === 'available').length;
  const totalRequestsCount = myRequests.length;

  return (
    <div className="space-y-6 sm:space-y-8">
      <RecommendationModal
        isOpen={showRecModal}
        onClose={() => setShowRecModal(false)}
        requestedBookTitle={lastRequestedBook}
        requestedBookDept={lastRequestedBookDept}
      />

      <div
        className="relative rounded-2xl overflow-hidden border border-gray-200 shadow-lg bg-cover bg-center"
        style={{ backgroundImage: `url(${libraryImage})` }}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/70 via-blue-900/30 to-white/0"></div>
        <div className="relative z-10 px-4 py-6 sm:px-6 sm:py-8 md:px-10 md:py-10">
          <p className="text-sm uppercase tracking-widest text-blue-200 font-semibold mb-2">Smart Library Dashboard</p>
          <h1 className="text-2xl sm:text-4xl md:text-5xl font-extrabold text-white mb-3">Discover, Request, and Track Books</h1>
          <p className="max-w-2xl text-sm md:text-base text-blue-100 mb-6">Search the catalog, place book requests, and monitor borrow/return activity from one place.</p>
          <div className="flex flex-wrap items-center gap-4 md:gap-6">
            <button className="bg-white text-blue-700 font-semibold px-5 py-2.5 rounded-lg shadow-sm hover:shadow-md border border-transparent transition-all">
              Browse Library
            </button>
            <div className="inline-flex items-center gap-4">
              <div className="bg-white/20 text-white px-4 py-2 rounded-lg">
                <p className="text-xs uppercase tracking-wider leading-tight">Available books</p>
                <p className="text-xl font-bold">{availableBooksCount}</p>
              </div>
              <div className="bg-white/20 text-white px-4 py-2 rounded-lg">
                <p className="text-xs uppercase tracking-wider leading-tight">My total requests</p>
                <p className="text-xl font-bold">{totalRequestsCount}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Welcome back, {user?.name || 'Student'}</h1>
          <p className="text-gray-600">Continue your research or explore library discoveries.</p>
        </div>
      </div>

      {/* ==============================
           BROWSE TAB
         ============================== */}
      {activeTab === 'browse' && (
        <div className="space-y-8 animate-fadeIn">
          <SearchBar value={searchQuery} onChange={setSearchQuery} />

          {recommendations?.books?.length > 0 && (
            <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-blue-50 p-4 sm:p-8 rounded-2xl border border-blue-200 shadow-lg relative overflow-hidden">
              {/* Background pattern */}
              <div className="absolute inset-0 opacity-5">
                <div className="absolute top-4 right-4 w-32 h-32 bg-blue-400 rounded-full blur-3xl"></div>
                <div className="absolute bottom-4 left-4 w-24 h-24 bg-indigo-400 rounded-full blur-2xl"></div>
              </div>

              <div className="relative z-10">
                <div className="text-center mb-8">
                  <h2 className="text-xl sm:text-3xl font-bold mb-2 flex items-center justify-center text-blue-900">
                    <Star className="mr-2 sm:mr-3 text-blue-600 w-6 h-6 sm:w-8 sm:h-8 fill-current animate-pulse" />
                    Recommended for You
                  </h2>
                  <p className="text-blue-700 text-sm sm:text-lg">Personalized picks based on your interests</p>
                </div>

                {/* Recommendations Table */}
                <div className="bg-white rounded-xl shadow-sm border border-blue-100 overflow-x-auto">
                  <table className="min-w-[680px] w-full divide-y divide-gray-200">
                    <thead className="bg-gradient-to-r from-blue-50 to-indigo-50">
                      <tr>
                        <th className="px-3 sm:px-6 py-4 text-left text-xs font-semibold text-blue-900 uppercase tracking-wider">
                          Book Title
                        </th>
                        <th className="px-3 sm:px-6 py-4 text-left text-xs font-semibold text-blue-900 uppercase tracking-wider">
                          Author
                        </th>
                        <th className="px-3 sm:px-6 py-4 text-left text-xs font-semibold text-blue-900 uppercase tracking-wider">
                          Book ID
                        </th>
                        <th className="px-3 sm:px-6 py-4 text-center text-xs font-semibold text-blue-900 uppercase tracking-wider">
                          Recommendation
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-100">
                      {recommendations.books.map((book, index) => (
                        <tr key={book.id} className={`hover:bg-blue-50 transition-colors ${index % 2 === 0 ? 'bg-white' : 'bg-blue-25'}`}>
                          <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="bg-blue-100 p-2 rounded-lg mr-3">
                                <BookOpen className="text-blue-600 w-5 h-5" />
                              </div>
                              <div>
                                <div className="text-sm font-semibold text-gray-900">{book.title}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {book.author}
                          </td>
                          <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                            {book.book_id}
                          </td>
                          <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-center">
                            <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold">
                              <Star className="w-4 h-4 fill-current" />
                              AI Recommended
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Summary */}
                <div className="mt-6 text-center">
                  <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 px-4 py-2 rounded-lg border border-blue-200">
                    <TrendingUp className="w-5 h-5" />
                    <span className="font-medium">
                      {recommendations.books.length} personalized recommendation{recommendations.books.length !== 1 ? 's' : ''} just for you
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="bg-white p-4 sm:p-6 rounded-xl border border-gray-100 shadow-sm">
            <h2 className="text-xl sm:text-2xl font-bold mb-6 flex items-center text-gray-800">
              <Book className="mr-2 text-green-600 w-6 h-6" />
              Available Books
            </h2>

            {filteredBooks.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <p>No books found matching your search.</p>
              </div>
            ) : (
              <div className="overflow-x-auto bg-white rounded-xl shadow-sm border border-gray-100">
                <table className="min-w-[700px] w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 sm:px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Book Title</th>
                      <th className="px-3 sm:px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Author</th>
                      <th className="px-3 sm:px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Genre</th>
                      <th className="px-3 sm:px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Inventory ID</th>
                      <th className="px-3 sm:px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredBooks.map(book => (
                      <tr key={book.id} className="hover:bg-blue-50">
                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{book.title}</div>
                        </td>
                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-600">{book.author}</td>
                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-600">{book.genre || 'N/A'}</td>
                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">{book.book_id}</td>
                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-sm text-center">
                          <button
                            onClick={() => handleRequest(book.id, book.title, book.department)}
                            disabled={actionLoading || book.status !== 'available'}
                            className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition ${
                              actionLoading || book.status !== 'available'
                                ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                                : 'bg-blue-600 hover:bg-blue-700 text-white'
                            }`}
                          >
                            {book.status === 'available' ? (actionLoading ? 'Requesting...' : 'Request') : 'Unavailable'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ==============================
           HISTORY TAB
         ============================== */}
      {activeTab === 'history' && (
        <div className="bg-white p-4 sm:p-6 rounded-xl border border-gray-100 shadow-sm animate-fadeIn">
          <h2 className="text-xl sm:text-2xl font-bold mb-6 flex items-center text-gray-800">
            <ClipboardList className="mr-2 text-purple-600 w-6 h-6" />
            Request History
          </h2>

          {myRequests.length === 0 ? (
            <div className="text-center py-16">
              <div className="bg-gray-50 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <ClipboardList className="text-gray-300 text-3xl" />
              </div>
              <h3 className="text-lg font-medium text-gray-900">
                No requests yet
              </h3>
              <p className="text-gray-500 mt-1">
                Books you request will appear here.
              </p>
              <button
                onClick={() => navigate('?tab=browse')}
                className="mt-4 text-blue-600 font-medium hover:underline"
              >
                Browse Books
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white border border-gray-200 rounded-xl">
                <thead className="bg-blue-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-blue-700 uppercase tracking-wide">Book</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-blue-700 uppercase tracking-wide">Author</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-blue-700 uppercase tracking-wide">Student</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-blue-700 uppercase tracking-wide">Request Date</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-blue-700 uppercase tracking-wide">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {myRequests.map((req, index) => (
                    <tr key={req.allocation_id ?? req.id ?? `req-${index}`} className="hover:bg-blue-50 transition-colors">
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{req.book_name || req.book?.title}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{req.book_author || req.book?.author || 'N/A'}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{req.user_name || user?.first_name + ' ' + user?.last_name}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{formatDate(req.created_at || req.requested_at)}</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${
                          req.status === 'approved' ? 'bg-green-100 text-green-700' :
                          req.status === 'rejected' ? 'bg-red-100 text-red-700' :
                          req.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {req.status?.charAt(0).toUpperCase() + req.status?.slice(1) || 'Unknown'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StudentDashboard;
