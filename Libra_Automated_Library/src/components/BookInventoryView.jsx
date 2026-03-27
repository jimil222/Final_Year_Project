import { useState, useEffect, useRef } from 'react';
import { getBookInventory } from '../utils/api';
import { useNotification } from '../hooks/useNotifications';
import { Search, RefreshCw, Filter } from 'lucide-react';

const BookInventoryView = () => {
  const { addNotification } = useNotification();
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [filteredBooks, setFilteredBooks] = useState([]);
  const lastInventorySignatureRef = useRef('');
  const isCheckingRef = useRef(false);

  const buildInventorySignature = (items) => {
    return items
      .map((book) => (
        `${book.book_id}:${book.status}:${book.updated_at}:${book.allocation_id || ''}:${book.allocation_status || ''}`
      ))
      .join('|');
  };

  const loadInventory = async (showLoader = true, onlyUpdateOnChange = false) => {
    if (showLoader) {
      setLoading(true);
    }

    try {
      const data = await getBookInventory(statusFilter || null, null);
      const nextSignature = buildInventorySignature(data);
      const hasChanged = nextSignature !== lastInventorySignatureRef.current;

      if (!onlyUpdateOnChange || hasChanged || lastInventorySignatureRef.current === '') {
        setBooks(data);
        setFilteredBooks(data);
      }

      lastInventorySignatureRef.current = nextSignature;
      return hasChanged;
    } catch (error) {
      console.error('Failed to load inventory:', error);
      if (showLoader) {
        addNotification(error.message || 'Failed to load book inventory', 'error');
      }
      return false;
    } finally {
      if (showLoader) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    loadInventory(true, false);
  }, [statusFilter]);

  // Check inventory periodically, but only update UI when data actually changes.
  useEffect(() => {
    const interval = setInterval(async () => {
      if (isCheckingRef.current) {
        return;
      }

      isCheckingRef.current = true;
      try {
        await loadInventory(false, true);
      } finally {
        isCheckingRef.current = false;
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [statusFilter]);

  // Apply local search filtering over server-filtered inventory data.
  useEffect(() => {
    if (!searchQuery) {
      setFilteredBooks(books);
      return;
    }

    let filtered = books;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(book =>
        (book.book_name && book.book_name.toLowerCase().includes(query)) ||
        (book.author && book.author.toLowerCase().includes(query))
      );
    }

    setFilteredBooks(filtered);
  }, [searchQuery, books]);

  const getStatusColor = (status) => {
    const colors = {
      AVAILABLE: 'bg-green-100 text-green-800 border-green-300',
      RESERVED: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      BORROWED: 'bg-blue-100 text-blue-800 border-blue-300',
      MAINTENANCE: 'bg-red-100 text-red-800 border-red-300'
    };
    return colors[status] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getStatusIcon = (status) => {
    const icons = {
      AVAILABLE: '✓',
      RESERVED: '⏳',
      BORROWED: '📖',
      MAINTENANCE: '⚠️'
    };
    return icons[status] || '•';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Book Inventory</h2>
        <p className="text-gray-600">View and manage all books in the library</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 space-y-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search Bar */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search by book name or author..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-100 focus:border-blue-400 outline-none text-sm"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-100 focus:border-blue-400 outline-none text-sm bg-white"
          >
            <option value="AVAILABLE,RESERVED">Available + Reserved</option>
            <option value="">All Status</option>
            <option value="AVAILABLE">Available</option>
            <option value="RESERVED">Reserved</option>
            <option value="BORROWED">Borrowed</option>
            <option value="MAINTENANCE">Maintenance</option>
          </select>

          {/* Refresh Button */}
          <button
            onClick={() => loadInventory(true, false)}
            disabled={loading}
            className="px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-all inline-flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>

        {/* Results summary */}
        <div className="text-sm text-gray-600 flex items-center gap-2">
          <Filter className="w-4 h-4" />
          Showing <strong>{filteredBooks.length}</strong> of <strong>{books.length}</strong> books
        </div>
      </div>

      {/* Books Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {filteredBooks.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Book Name</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Author</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Status</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">NFC Tag</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Current Holder</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredBooks.map((book) => (
                  <tr key={book.book_id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <span className="font-medium text-gray-900">{book.book_name}</span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{book.author || '—'}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(book.status)}`}>
                        <span>{getStatusIcon(book.status)}</span>
                        {book.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 font-mono text-xs">{book.nfc_tag_id}</td>
                    <td className="px-4 py-3">
                      {book.allocation_user_name ? (
                        <div className="text-gray-900 font-medium">
                          {book.allocation_user_name}
                          <div className="text-xs text-gray-500">{book.allocation_user_email}</div>
                        </div>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-4 py-12 text-center">
            <p className="text-gray-500">
              {books.length === 0 ? 'No books in inventory' : 'No books match your search'}
            </p>
          </div>
        )}
      </div>

      {/* Stats */}
      {books.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <div className="text-sm text-green-600 font-medium">Available</div>
            <div className="text-2xl font-bold text-green-700 mt-1">
              {books.filter(b => b.status === 'AVAILABLE').length}
            </div>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
            <div className="text-sm text-yellow-600 font-medium">Reserved</div>
            <div className="text-2xl font-bold text-yellow-700 mt-1">
              {books.filter(b => b.status === 'RESERVED').length}
            </div>
          </div>
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="text-sm text-blue-600 font-medium">Borrowed</div>
            <div className="text-2xl font-bold text-blue-700 mt-1">
              {books.filter(b => b.status === 'BORROWED').length}
            </div>
          </div>
          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
            <div className="text-sm text-red-600 font-medium">Maintenance</div>
            <div className="text-2xl font-bold text-red-700 mt-1">
              {books.filter(b => b.status === 'MAINTENANCE').length}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BookInventoryView;
