// Mock API functions - replace with actual API calls when backend is ready
import { dummyBooks } from '../data/dummyBooks';
import { dummyRequests } from '../data/dummyRequests';
import { dummyRecommendations } from '../data/dummyRecommendations';
import { dummyRobotStatus } from '../data/dummyRobotStatus';
import { dummyUsers } from '../data/dummyUsers';

// Import dummyRequests to ensure we're modifying the actual array
// This is already imported above, but we need to make sure we're working with the actual reference

const delay = (ms = 500) => new Promise((resolve) => setTimeout(resolve, ms));

// LocalStorage keys
const STORAGE_KEY_REQUESTS = 'libra_requests';

// Helper functions for localStorage persistence
const getStoredRequests = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY_REQUESTS);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error('Error loading requests from localStorage:', error);
  }
  return null;
};

const saveRequestsToStorage = (requests) => {
  try {
    localStorage.setItem(STORAGE_KEY_REQUESTS, JSON.stringify(requests));
  } catch (error) {
    console.error('Error saving requests to localStorage:', error);
  }
};

// Get current requests array (from localStorage or return empty array)
const getRequestsArray = () => {
  const stored = getStoredRequests();
  // Return stored requests if they exist, otherwise return empty array
  // Don't initialize with dummy data - start fresh for new installations
  if (stored !== null) {
    // Validate it's an array
    if (Array.isArray(stored)) {
      // Filter out any invalid requests (missing required fields)
      const validRequests = stored.filter(req =>
        req &&
        typeof req.id !== 'undefined' &&
        typeof req.book_id !== 'undefined' &&
        typeof req.student_id !== 'undefined' &&
        typeof req.status !== 'undefined'
      );
      // If we filtered out invalid requests, save the cleaned array
      if (validRequests.length !== stored.length) {
        console.warn(`Filtered out ${stored.length - validRequests.length} invalid requests`);
        saveRequestsToStorage(validRequests);
      }
      return validRequests;
    } else {
      // Not an array - clear it and return empty
      console.error('libra_requests is not an array, clearing...');
      localStorage.removeItem(STORAGE_KEY_REQUESTS);
      return [];
    }
  }
  // First time - return empty array, don't populate with dummy data
  return [];
};

// Helper to enrich request with book data
const enrichRequestWithBook = (request) => {
  // Try to find book by ID, handle both number and string comparisons
  const bookId = typeof request.book_id === 'string' ? parseInt(request.book_id) : request.book_id;
  const book = dummyBooks.find((b) => b.id === bookId || b.id === request.book_id);

  // If we found a book, use it. Otherwise, try to preserve the existing book data.
  // If no book data exists at all, create a minimal book object to prevent display issues
  const enrichedBook = book || request.book || {
    id: bookId || request.book_id,
    book_id: 'N/A',
    title: 'Unknown Book',
    author: 'Unknown Author'
  };

  return {
    ...request,
    book_id: bookId || request.book_id, // Ensure book_id is consistently a number
    book: enrichedBook
  };
};

// Authentication
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Authentication
export const login = async (email, password, role = 'student') => {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password, role }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Login failed');
  }

  const data = await response.json();
  // Map backend fields to frontend expectations
  const user = {
    ...data,
    id: data.user_id, // Map user_id to id
    role: data.role || (data.email.includes('admin') ? 'admin' : 'student'),
    field_of_study: data.department,
    roll_no: data.roll_no || null // Handle optional roll_no for admins
  };
  return { user, token: data.access_token };
};

export const register = async (userData) => {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Registration failed');
  }

  const data = await response.json();
  const user = {
    ...data,
    id: data.user_id, // Map user_id to id
    role: data.role || 'student',
    field_of_study: data.department,
    roll_no: data.roll_no || null // Handle optional roll_no for admins
  };
  return { user, token: data.access_token };
};



export const verifyToken = async (token) => {
  const response = await fetch(`${API_URL}/student/me`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    throw new Error('Token invalid');
  }

  const data = await response.json();
  // Map fields
  return {
    ...data,
    id: data.user_id,
    role: data.role || (data.email.includes('admin') ? 'admin' : 'student'),
    field_of_study: data.department, // Map department to field_of_study
    roll_no: data.roll_no || null // Handle optional roll_no
  };
};

// Books - Now using backend API
export const getBooks = async (query = '') => {
  const token = localStorage.getItem('token');
  if (!token) return [];

  try {
    const response = await fetch(`${API_URL}/books/`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      console.error('Failed to fetch books');
      return [];
    }

    const books = await response.json();

    // Map backend fields to frontend format
    return books.map(book => ({
      id: book.book_id,
      book_id: `BOOK-${book.book_id}`,
      title: book.book_name,
      author: book.author || 'Unknown Author',
      status: book.status.toLowerCase(),
      genre: 'General', // Backend doesn't have genre yet
      shelf_number: book.shelf_id,
      nfc_tag_id: book.nfc_tag_id,
      allocation: book.allocation, // Include allocation info if present
      created_at: book.created_at,
      updated_at: book.updated_at
    })).filter(book => {
      // Filter by query if provided
      if (!query) return true;
      const lowerQuery = query.toLowerCase();
      return book.title.toLowerCase().includes(lowerQuery) ||
        book.author.toLowerCase().includes(lowerQuery) ||
        book.book_id.toLowerCase().includes(lowerQuery);
    });
  } catch (error) {
    console.error('Error fetching books:', error);
    return [];
  }
};

export const getBookById = async (id) => {
  await delay();
  return dummyBooks.find((book) => book.id === parseInt(id));
};

// Requests
// Requests - Now using backend
export const getRequests = async (studentId = null, status = null) => {
  const token = localStorage.getItem('token');
  if (!token) return [];

  try {
    // For student dashboard, we want the current user's allocations
    const response = await fetch(`${API_URL}/allocations/my`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      console.error('Failed to fetch requests');
      return [];
    }

    let requests = await response.json();

    // Filter by status if provided (optional)
    if (status) {
      requests = requests.filter(req => req.status.toLowerCase() === status.toLowerCase());
    }

    return requests;
  } catch (error) {
    console.error('Error fetching requests:', error);
    return [];
  }
};



export const updateRequestStatus = async (requestId, status) => {
  await delay();
  const currentRequests = getRequestsArray();
  const requestIndex = currentRequests.findIndex((req) => req.id === parseInt(requestId));
  if (requestIndex !== -1) {
    const request = currentRequests[requestIndex];
    const bookId = request.book_id;

    // Find the book in dummyBooks array (for fallback display)
    const book = dummyBooks.find((b) => b.id === bookId);

    if (status === 'approved') {
      try {
        // Call the backend to approve (PENDING → RESERVED)
        await approveRequest(bookId);

        // Update request status
        request.status = 'approved';
        request.approved_at = new Date().toISOString();

        // Update local book status for immediate UI feedback
        if (book) {
          book.status = 'reserved';
          book.reserved_by = request.student_id;
        }
      } catch (error) {
        console.error('Failed to reserve book on backend:', error);
        // Still update locally even if backend fails (for now)
        request.status = 'approved';
        request.approved_at = new Date().toISOString();
        if (book) {
          book.status = 'reserved';
          book.reserved_by = request.student_id;
        }
      }
    } else if (status === 'rejected') {
      // Reject the request
      request.status = 'rejected';

      // Keep book available (no backend call needed for rejection)
      if (book) {
        book.status = 'available';
        book.reserved_by = null;
      }
    }

    saveRequestsToStorage(currentRequests);
    return enrichRequestWithBook(request);
  }
  return null;
};

// Recommendations
export const getRecommendations = async (studentId, fieldOfStudy = null) => {
  const token = localStorage.getItem('token');
  if (!token) return null;

  const response = await fetch(`${API_URL}/student/recommendations`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    console.error('Failed to fetch recommendations');
    return null;
  }

  const data = await response.json();
  console.log('Recommendations response:', data);
  return data;
};

// Get top books by genre
export const getTopBooksByGenre = async () => {
  await delay();
  const genreMap = {};

  dummyBooks.forEach(book => {
    if (!genreMap[book.genre]) {
      genreMap[book.genre] = [];
    }
    if (book.status === 'available') {
      genreMap[book.genre].push(book);
    }
  });

  // Get top 3 books from each genre
  const topByGenre = {};
  Object.keys(genreMap).forEach(genre => {
    topByGenre[genre] = genreMap[genre].slice(0, 3);
  });

  return topByGenre;
};

// Robot Status
export const getRobotStatus = async () => {
  await delay(200);
  return dummyRobotStatus;
};

// Admin: get shelves for Add Book dropdown
export const getShelves = async () => {
  const token = localStorage.getItem('token');
  if (!token) return [];
  try {
    const response = await fetch(`${API_URL}/books/shelves`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) return [];
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch shelves:', error);
    return [];
  }
};

// Admin: get last NFC scan (for Add Book - Scan NFC button). No auth required by backend.
export const getLastNfcScan = async () => {
  try {
    const headers = {};
    const token = localStorage.getItem('token');
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const response = await fetch(`${API_URL}/nfc/last-scan`, { headers });
    if (!response.ok) return { nfc_tag_id: null, scanned_at: null };
    return await response.json();
  } catch (error) {
    console.warn('getLastNfcScan failed:', error);
    return { nfc_tag_id: null, scanned_at: null };
  }
};

// Simulate an NFC scan (for testing without reader). POSTs to backend so next poll gets it.
export const simulateNfcScan = async (uid = null) => {
  const nfc_tag_id = uid || 'TEST-' + Math.random().toString(36).slice(2, 10).toUpperCase();
  const response = await fetch(`${API_URL}/nfc/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nfc_tag_id }),
  });
  if (!response.ok) throw new Error('Simulate scan failed');
  return nfc_tag_id;
};

// Get book by NFC tag ID
export const getBookByNfcId = async (nfc_tag_id) => {
  try {
    const headers = {};
    const token = localStorage.getItem('token');
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const normalizedNfcTagId = String(nfc_tag_id || '').trim().toUpperCase().replace(/\s+/g, '');

    if (!normalizedNfcTagId) {
      return null;
    }

    // Try to fetch from backend first
    try {
      const response = await fetch(`${API_URL}/books/nfc/${encodeURIComponent(normalizedNfcTagId)}`, { headers });
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.warn('Backend NFC lookup failed, falling back to mock data');
    }

    // Fallback to mock data - search in dummyBooks
    const book = dummyBooks.find(b => String(b.book_id).toUpperCase() === normalizedNfcTagId || b.nfc_tag_id === normalizedNfcTagId);
    return book || null;
  } catch (error) {
    console.warn('getBookByNfcId error:', error);
    return null;
  }
};

// Admin: create book (backend POST /books)
export const createBook = async (bookData) => {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Not authenticated');
  const response = await fetch(`${API_URL}/books/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      book_name: bookData.book_name,
      author: bookData.author || null,
      nfc_tag_id: bookData.nfc_tag_id,
      shelf_id: bookData.shelf_id
    })
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to add book');
  }
  return await response.json();
};

// Admin: addBook alias for compatibility (calls createBook)
export const addBook = async (bookData) => {
  return createBook({
    book_name: bookData.title || bookData.book_name,
    author: bookData.author || null,
    nfc_tag_id: bookData.nfc_tag_id || bookData.book_id,
    shelf_id: bookData.shelf_id || parseInt(bookData.bin_id, 10)
  });
};

// NFC Operations - can accept book ID or book name
export const nfcIssue = async (bookIdentifier, studentId) => {
  await delay(1000);
  // Try to find by book_id, id, or title (case insensitive)
  const book = dummyBooks.find((b) =>
    b.book_id === bookIdentifier ||
    b.id === parseInt(bookIdentifier) ||
    b.title.toLowerCase() === bookIdentifier.toLowerCase()
  );
  if (!book) throw new Error('Book not found. Please check the Book ID or Book Name.');

  // If book is available and being directly issued, create a request record for tracking
  if (book.status === 'available') {
    const currentRequests = getRequestsArray();
    // Check if there's already a pending request for this book by this student
    const existingRequestIndex = currentRequests.findIndex(
      req => req.book_id === book.id && req.student_id === studentId && req.status === 'pending'
    );

    if (existingRequestIndex === -1) {
      // Create an auto-approved request for direct issue tracking
      const maxId = currentRequests.length > 0
        ? Math.max(...currentRequests.map(r => r.id || 0))
        : 0;
      const newRequest = {
        id: maxId + 1,
        student_id: studentId,
        book_id: book.id,
        status: 'approved',
        requested_at: new Date().toISOString(),
        approved_at: new Date().toISOString(),
        book: book
      };
      const updatedRequests = [...currentRequests, newRequest];
      saveRequestsToStorage(updatedRequests);
    } else {
      // If there's a pending request, auto-approve it
      const existingRequest = currentRequests[existingRequestIndex];
      existingRequest.status = 'approved';
      existingRequest.approved_at = new Date().toISOString();
      saveRequestsToStorage(currentRequests);
    }
  }

  if (book.status !== 'available' && book.status !== 'reserved') {
    throw new Error('Book is not available for issue');
  }
  book.status = 'issued';
  book.reserved_by = studentId;
  return { success: true, book, dueDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000) };
};

export const nfcReturn = async (bookIdentifier) => {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Not authenticated');

  try {
    const response = await fetch(`${API_URL}/books/return`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ nfc_tag_id: bookIdentifier })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to return book');
    }

    const data = await response.json();
    return {
      success: true,
      book: { book_name: data.book_name },
      returnTime: data.return_time,
      wasOverdue: data.was_overdue
    };
  } catch (error) {
    throw error;
  }
};

// Book reservation (new endpoint - creates PENDING request)
export const requestBook = async (bookId) => {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Not authenticated');

  try {
    const response = await fetch(`${API_URL}/books/${bookId}/request`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to request book');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

// NFC borrow (new endpoint)
export const nfcBorrow = async (nfcTagId) => {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Not authenticated');

  try {
    const response = await fetch(`${API_URL}/books/borrow`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ nfc_tag_id: nfcTagId })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to borrow book');
    }

    const data = await response.json();
    return {
      success: true,
      book: { book_name: data.book_name },
      dueDate: data.due_date,
      transactionId: data.transaction_id
    };
  } catch (error) {
    throw error;
  }
};

// Get user's allocations
export const getMyAllocations = async () => {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Not authenticated');

  try {
    const response = await fetch(`${API_URL}/allocations/my`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      console.error('Failed to fetch allocations');
      return [];
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching allocations:', error);
    return [];
  }
};

// Get user's transaction history
export const getMyTransactions = async () => {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Not authenticated');

  try {
    const response = await fetch(`${API_URL}/allocations/transactions/my`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      console.error('Failed to fetch transactions');
      return [];
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching transactions:', error);
    return [];
  }
};

// Admin: Get all allocations
export const getAllAllocations = async () => {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Not authenticated');

  try {
    const response = await fetch(`${API_URL}/allocations/all`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      console.error('Failed to fetch allocations');
      return [];
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching allocations:', error);
    return [];
  }
};

// Admin: Approve request (PENDING→RESERVED)
export const approveRequest = async (bookId) => {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Not authenticated');

  try {
    const response = await fetch(`${API_URL}/books/${bookId}/approve-request`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to approve request');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

// Admin: Reject request (PENDING→Deleted)
export const rejectRequest = async (bookId) => {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Not authenticated');

  try {
    const response = await fetch(`${API_URL}/books/${bookId}/reject-request`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to reject request');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

// Admin: Get book inventory with filters
export const getBookInventory = async (status = null, search = null, skip = 0, limit = 100) => {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Not authenticated');

  try {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    params.append('skip', skip);
    params.append('limit', limit);

    const response = await fetch(`${API_URL}/books/admin/inventory?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch book inventory');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching book inventory:', error);
    throw error;
  }
};

// Admin: Get pending book requests
export const getPendingRequests = async (search = null, skip = 0, limit = 100) => {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Not authenticated');

  try {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('skip', skip);
    params.append('limit', limit);

    const response = await fetch(`${API_URL}/books/admin/pending-requests?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch pending requests');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching pending requests:', error);
    throw error;
  }
};

