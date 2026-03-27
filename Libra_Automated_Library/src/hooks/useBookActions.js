import { useState } from 'react';
import { requestBook as apiRequestBook, updateRequestStatus, nfcBorrow, nfcReturn } from '../utils/api';
import { useNotification } from '../context/NotificationContext';

export const useBookActions = () => {
  const [loading, setLoading] = useState(false);
  const { addNotification } = useNotification();

  const requestBook = async (student, bookId) => {
    setLoading(true);
    try {
      // Call new backend API (creates PENDING allocation in database)
      await apiRequestBook(bookId);
      addNotification('Book request submitted successfully! Waiting for admin approval.', 'success');
    } catch (error) {
      addNotification(error.message || 'Failed to request book', 'error');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const approveRequest = async (requestId) => {
    setLoading(true);
    try {
      const request = await updateRequestStatus(requestId, 'approved');
      addNotification('Request approved successfully!', 'success');
      return request;
    } catch (error) {
      addNotification(error.message || 'Failed to approve request', 'error');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const rejectRequest = async (requestId) => {
    setLoading(true);
    try {
      const request = await updateRequestStatus(requestId, 'rejected');
      addNotification('Request rejected', 'info');
      return request;
    } catch (error) {
      addNotification(error.message || 'Failed to reject request', 'error');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const handleNfcIssue = async (bookId, studentId) => {
    setLoading(true);
    try {
      const result = await nfcBorrow(bookId);
      addNotification(`Book borrowed successfully! Due date: ${new Date(result.dueDate).toLocaleDateString()}`, 'success');
      return result;
    } catch (error) {
      addNotification(error.message || 'Failed to borrow book', 'error');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const handleNfcReturn = async (bookId) => {
    setLoading(true);
    try {
      const result = await nfcReturn(bookId);
      addNotification('Book returned successfully!', 'success');
      return result;
    } catch (error) {
      addNotification(error.message || 'Failed to return book', 'error');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    requestBook,
    approveRequest,
    rejectRequest,
    handleNfcIssue,
    handleNfcReturn
  };
};

