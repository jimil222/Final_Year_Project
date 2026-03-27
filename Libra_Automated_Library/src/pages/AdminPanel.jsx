import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useBookContext } from '../context/BookContext';
import {
  getAllAllocations,
  approveRequest,
  rejectRequest,
  addBook,
  getShelves,
  getLastNfcScan,
  simulateNfcScan,
} from '../utils/api';
import BookInventoryView from '../components/BookInventoryView';
import PendingRequestsView from '../components/PendingRequestsView';
import ScanInventoryView from '../components/ScanInventoryView';
import Modal from '../components/Modal';
import { useNotification } from '../hooks/useNotifications';
import { formatDate } from '../utils/helpers';
import { Search, RefreshCw, Radio, CheckCircle, XCircle, Loader2, Plus, BookOpen, Hourglass } from 'lucide-react';

const AdminPanel = () => {
  const [searchParams] = useSearchParams();
  const { loadBooks } = useBookContext();
  const { addNotification } = useNotification();
  const [activeTab, setActiveTab] = useState('requests');
  const [isAddBookOpen, setIsAddBookOpen] = useState(false);
  const [allocations, setAllocations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [shelves, setShelves] = useState([]);
  const [scanningNfc, setScanningNfc] = useState(false);
  const [newBook, setNewBook] = useState({
    title: '',
    author: '',
    nfc_tag_id: '',
    shelf_id: ''
  });

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [deptFilter, setDeptFilter] = useState('All Departments');

  const loadAllocations = async () => {
    setLoading(true);
    try {
      const data = await getAllAllocations();
      // Filter for PENDING status (awaiting admin approval)
      const pendingRequests = data.filter(a => a.status === 'PENDING');
      setAllocations(pendingRequests);
    } catch (error) {
      console.error('Failed to load allocations:', error);
      addNotification('Failed to load requests', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllocations();
  }, []);

  useEffect(() => {
    const load = async () => {
      const list = await getShelves();
      setShelves(Array.isArray(list) ? list : []);
    };
    load();
  }, []);

  // Reload allocations when switching to requests tab
  useEffect(() => {
    if (activeTab === 'requests') {
      loadAllocations();
    }
  }, [activeTab]);

  useEffect(() => {
    const tab = searchParams.get('tab');
    const validTabs = ['inventory', 'requests', 'add-book', 'robot', 'scan-inventory'];
    if (validTabs.includes(tab)) {
      setActiveTab(tab);
    } else {
      setActiveTab('requests');
    }
  }, [searchParams]);

  // ==============================
  // AUTO REFRESH PENDING REQUESTS
  // ==============================
  useEffect(() => {
    if (activeTab !== 'requests') return;

    const interval = setInterval(() => {
      loadAllocations();
    }, 3000); // refresh every 3 seconds

    return () => clearInterval(interval);
  }, [activeTab]);


  // Poll for NFC scan when Scan button in Add Book modal is active
  useEffect(() => {
    if (!scanningNfc || !isAddBookOpen) return;
    let cancelled = false;
    const poll = async () => {
      const res = await getLastNfcScan();
      if (cancelled) return;
      if (res && res.nfc_tag_id) {
        setNewBook(prev => ({ ...prev, nfc_tag_id: res.nfc_tag_id }));
        setScanningNfc(false);
        addNotification('NFC tag scanned: ' + res.nfc_tag_id, 'success');
      }
    };
    poll();
    const interval = setInterval(poll, 800);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [scanningNfc, isAddBookOpen, addNotification]);

  const handleApprove = async (bookId) => {
    setLoading(true);
    try {
      await approveRequest(bookId); // Fixed: was calling approveReservation
      addNotification('Request approved successfully!', 'success');
      loadAllocations();
      loadBooks();
    } catch (error) {
      addNotification(error.message || 'Failed to approve request', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (bookId) => {
    setLoading(true);
    try {
      await rejectRequest(bookId);
      addNotification('Request rejected successfully', 'info');
      loadAllocations();
      loadBooks();
    } catch (error) {
      addNotification(error.message || 'Failed to reject request', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAddBook = async (e) => {
    e.preventDefault();
    if (!newBook.nfc_tag_id) {
      addNotification('NFC ID is required. Shelf will be auto-assigned if not selected.', 'error');
      return;
    }
    try {
      const bookPayload = {
        title: newBook.title,
        author: newBook.author,
        nfc_tag_id: newBook.nfc_tag_id
      };
      // Only include shelf_id if explicitly selected (not empty)
      if (newBook.shelf_id) {
        bookPayload.shelf_id = parseInt(newBook.shelf_id, 10);
      }
      await addBook(bookPayload);
      addNotification('Book added successfully!', 'success');
      setIsAddBookOpen(false);
      setNewBook({ title: '', author: '', nfc_tag_id: '', shelf_id: '' });
      loadBooks();
    } catch (error) {
      addNotification(error.message || 'Failed to add book', 'error');
    }
  };

  const closeAddBookModal = () => {
    setIsAddBookOpen(false);
    setNewBook({ title: '', author: '', nfc_tag_id: '', shelf_id: '' });
    setScanningNfc(false);
  };

  // Apply Search and Filters
  const filteredAllocations = allocations.filter(alloc => {
    const matchesSearch =
      (alloc.user_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (alloc.book_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (alloc.user_email || '').toLowerCase().includes(searchQuery.toLowerCase());

    // For department filter, we'd need to add dept info to allocations
    const matchesDept = deptFilter === 'All Departments';

    return matchesSearch && matchesDept;
  }).sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

  // Unique Departments for filter (simplified for now)
  const departments = ['All Departments'];

  return (
    <div className="space-y-6 font-['Inter']">
      <div>
        <div className="flex items-center gap-3">
          <BookOpen className="w-7 h-7 text-blue-600" />
          <h1 className="text-2xl md:text-2xl font-semibold font-['Poppins'] text-gray-900 leading-tight tracking-tight">
            Library <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">Management Hub</span>
          </h1>
        </div>
        <p className="text-sm md:text-sm text-gray-500 mt-3">Streamline operations and handle book requests efficiently</p>
      </div>

      {activeTab === 'inventory' && <BookInventoryView />}

      {activeTab === 'requests' && (
        <>
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Hourglass className="w-6 h-6 text-blue-600" />
              <h2 className="text-xl md:text-lg font-medium font-['Poppins'] text-gray-600 tracking-tight">Book Request Queue</h2>
            </div>
            <p className="text-gray-500 text-sm">Review and process student requests</p>
          </div>
          <PendingRequestsView onRequestsChanged={loadBooks} hideHeader />
        </>
      )}

      {activeTab === 'add-book' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-semibold font-['Poppins'] text-gray-900">Add New Book</h2>
              <p className="text-gray-500 text-sm mt-1">Add books to the library catalog</p>
            </div>
            <button
              onClick={() => setIsAddBookOpen(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold flex items-center gap-2"
            >
              <Plus size={20} />
              Add Book
            </button>
          </div>
        </div>
      )}

      {activeTab === 'robot' && (
        <div>
          <h2 className="text-lg font-semibold font-['Poppins'] text-gray-900 mb-6">Robot & Bin Monitoring</h2>
          <RobotStatus />
        </div>
      )}

      {activeTab === 'scan-inventory' && <ScanInventoryView />}

      {/* Add Book Modal */}
      <Modal
        isOpen={isAddBookOpen}
        onClose={closeAddBookModal}
        title="Add New Book"
      >
        {/* Single-step Add Book form (no NFC write) */}
        <form onSubmit={handleAddBook} className="space-y-5">
          <div>
            <label className="block text-gray-700 text-sm font-semibold mb-2">Book Title</label>
            <input
              type="text"
              value={newBook.title}
              onChange={(e) => setNewBook({ ...newBook, title: e.target.value })}
              required
              className="input-modern"
              placeholder="Enter book title"
            />
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-semibold mb-2">Author</label>
            <input
              type="text"
              value={newBook.author}
              onChange={(e) => setNewBook({ ...newBook, author: e.target.value })}
              className="input-modern"
              placeholder="Enter author name"
            />
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-semibold mb-2">Shelf <span className="text-gray-500 text-xs font-normal">(optional)</span></label>
            <select
              value={newBook.shelf_id}
              onChange={(e) => setNewBook({ ...newBook, shelf_id: e.target.value })}
              className="input-modern"
            >
              <option value="">Auto-assign to available shelf</option>
              {shelves.map((s) => (
                <option key={s.shelf_id} value={s.shelf_id}>
                  Shelf {s.shelf_number} (ID: {s.shelf_id})
                </option>
              ))}
            </select>
          </div>

          <div className="border-t border-gray-200 pt-4 mt-4">
            <p className="text-xs text-gray-600 mb-2">
              Link this book to an NFC tag by scanning its UID. The tag itself is not written to.
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={newBook.nfc_tag_id}
                onChange={(e) => setNewBook({ ...newBook, nfc_tag_id: e.target.value })}
                className="input-modern font-mono flex-1"
                placeholder="NFC Tag ID"
              />
              <button
                type="button"
                onClick={() => setScanningNfc(true)}
                className="px-3 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-sm font-medium whitespace-nowrap"
              >
                {scanningNfc ? 'Scanning…' : 'Scan Tag'}
              </button>
              <button
                type="button"
                onClick={async () => {
                  try {
                    const uid = await simulateNfcScan();
                    setScanningNfc(true);
                    addNotification('Test scan sent.', 'info');
                    setTimeout(() => setNewBook(prev => ({ ...prev, nfc_tag_id: uid })), 400);
                    setScanningNfc(false);
                  } catch (e) {
                    addNotification(e.message || 'Simulate failed', 'error');
                  }
                }}
                className="px-3 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-xs font-medium"
                title="Test without hardware"
              >
                Test
              </button>
            </div>
            <div className="flex space-x-3 mt-3">
              <button type="button" onClick={closeAddBookModal} className="btn-secondary flex-1">
                Cancel
              </button>
              <button type="submit" className="btn-primary flex-1">
                Add Book
              </button>
            </div>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default AdminPanel;

