import { useState, useEffect, useRef } from 'react';
import { getPendingRequests, approveRequest, rejectRequest } from '../utils/api';
import { useNotification } from '../hooks/useNotifications';
import { Search, RefreshCw, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { formatDate } from '../utils/helpers';

const PendingRequestsView = ({ onRequestsChanged, hideHeader = false }) => {
  const { addNotification } = useNotification();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processingId, setProcessingId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredRequests, setFilteredRequests] = useState([]);
  const knownRequestIdsRef = useRef(new Set());
  const isCheckingRef = useRef(false);

  const loadRequests = async ({ showLoader = true, query = searchQuery || null } = {}) => {
    if (showLoader) {
      setLoading(true);
    }

    try {
      const data = await getPendingRequests(query);
      setRequests(data);
      setFilteredRequests(data);
      knownRequestIdsRef.current = new Set(data.map((req) => req.allocation_id));
    } catch (error) {
      console.error('Failed to load pending requests:', error);
      addNotification(error.message || 'Failed to load pending requests', 'error');
    } finally {
      if (showLoader) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    loadRequests();

    // Background check: only update UI when a new pending request arrives.
    const interval = setInterval(async () => {
      if (isCheckingRef.current) {
        return;
      }

      isCheckingRef.current = true;
      try {
        const data = await getPendingRequests(null);
        const hasNewRequest = data.some((req) => !knownRequestIdsRef.current.has(req.allocation_id));

        if (hasNewRequest) {
          setRequests(data);
          setFilteredRequests(data);
          knownRequestIdsRef.current = new Set(data.map((req) => req.allocation_id));
          addNotification('New pending request received.', 'info');
        }
      } catch (error) {
        console.error('Background request check failed:', error);
      } finally {
        isCheckingRef.current = false;
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [addNotification]);

  // Apply search filter
  useEffect(() => {
    if (!searchQuery) {
      setFilteredRequests(requests);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = requests.filter(req =>
      (req.user_name && req.user_name.toLowerCase().includes(query)) ||
      (req.user_email && req.user_email.toLowerCase().includes(query)) ||
      (req.book_name && req.book_name.toLowerCase().includes(query))
    );

    setFilteredRequests(filtered);
  }, [searchQuery, requests]);

  const handleApprove = async (allocationId, bookId) => {
    setProcessingId(allocationId);
    try {
      await approveRequest(bookId);
      addNotification('Request approved successfully!', 'success');
      loadRequests();
      if (onRequestsChanged) onRequestsChanged();
    } catch (error) {
      addNotification(error.message || 'Failed to approve request', 'error');
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (allocationId, bookId) => {
    setProcessingId(allocationId);
    try {
      await rejectRequest(bookId);
      addNotification('Request rejected successfully', 'info');
      loadRequests();
      if (onRequestsChanged) onRequestsChanged();
    } catch (error) {
      addNotification(error.message || 'Failed to reject request', 'error');
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      {!hideHeader && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Pending Book Requests</h2>
          <p className="text-gray-600">Manage student book requests</p>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 space-y-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search Bar */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search by student or book name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-100 focus:border-blue-400 outline-none text-sm"
            />
          </div>

          {/* Refresh Button */}
          <button
            onClick={() => loadRequests()}
            disabled={loading}
            className="px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-all inline-flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>

        {/* Results summary */}
        <div className="text-sm text-gray-600">
          <strong>{filteredRequests.length}</strong> pending request{filteredRequests.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Requests List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-x-auto">
        {filteredRequests.length > 0 ? (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Book</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Author</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Student</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Department</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Requested</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {filteredRequests.map((request) => (
                <tr key={request.allocation_id}>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{request.book_name}</div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{request.book_author || 'Unknown'}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{request.user_name}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{request.user_department || '—'}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{formatDate(request.requested_at || request.created_at)}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-right flex flex-col sm:flex-row gap-2 justify-end">
                    <button
                      onClick={() => handleApprove(request.allocation_id, request.book_id)}
                      disabled={processingId === request.allocation_id}
                      className="px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all inline-flex items-center justify-center gap-1 text-xs sm:text-sm"
                    >
                      {processingId === request.allocation_id ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <CheckCircle className="w-3.5 h-3.5" />
                      )}
                      <span>Approve</span>
                    </button>
                    <button
                      onClick={() => handleReject(request.allocation_id, request.book_id)}
                      disabled={processingId === request.allocation_id}
                      className="px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all inline-flex items-center justify-center gap-1 text-xs sm:text-sm"
                    >
                      {processingId === request.allocation_id ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5" />
                      )}
                      <span>Reject</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-center p-10">
            <p className="text-xl font-medium text-gray-700 mb-4">All caught up! 🎉</p>
            <p className="text-md text-gray-600 mb-2">Everything has been processed successfully</p>
            <p className="text-gray-500 mb-2">
              {requests.length === 0 ? 'No pending requests' : 'No requests match your search'}
            </p>
            {requests.length === 0 && <p className="text-sm text-gray-400">• New requests will appear here</p>}
          </div>
        )}
      </div>

      {/* Stats Card */}
      {requests.length > 0 && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
          <div className="text-sm text-blue-700">
            <strong>{filteredRequests.length}</strong> request{filteredRequests.length !== 1 ? 's' : ''} awaiting approval
          </div>
        </div>
      )}
    </div>
  );
};

export default PendingRequestsView;
