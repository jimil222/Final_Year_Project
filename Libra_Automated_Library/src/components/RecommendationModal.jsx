import { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Lightbulb, Book } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

const RecommendationModal = ({ isOpen, onClose, requestedBookTitle, requestedBookDept }) => {
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(false);
    const { user } = useAuth();

    // Use Vite env var or default
    const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

    useEffect(() => {
        const fetchRecommendations = async () => {
            if (isOpen && requestedBookTitle) {
                setLoading(true);

                try {
                    const token = localStorage.getItem('token');
                    // Add department to query params if available
                    let url = `${API_URL}/student/recommend-similar?title=${encodeURIComponent(requestedBookTitle)}`;
                    if (requestedBookDept) {
                        url += `&department=${encodeURIComponent(requestedBookDept)}`;
                    }

                    const response = await axios.get(url, {
                        headers: { Authorization: `Bearer ${token}` }
                    }
                    );
                    setRecommendations(response.data.books || []);
                } catch (error) {
                    console.error("Failed to fetch similar books:", error);
                    setRecommendations([]);
                } finally {
                    setLoading(false);
                }
            }
        };

        fetchRecommendations();
    }, [isOpen, requestedBookTitle, requestedBookDept, API_URL]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            {/* Backdrop */}
            <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div
                    className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
                    aria-hidden="true"
                    onClick={onClose}
                ></div>

                {/* Modal Panel */}
                <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
                    <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                        <div className="sm:flex sm:items-start">
                            <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100 sm:mx-0 sm:h-10 sm:w-10">
                                <Lightbulb className="h-6 w-6 text-yellow-600" aria-hidden="true" />
                            </div>
                            <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                                <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                                    You requested "{requestedBookTitle}"
                                </h3>
                                <div className="mt-2">
                                    <p className="text-sm text-gray-500">
                                        Here are some other books you might like based on your request:
                                    </p>
                                </div>

                                {/* Content Area */}
                                <div className="mt-4 min-h-[150px]">
                                    {loading ? (
                                        <div className="flex justify-center items-center py-8">
                                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500"></div>
                                        </div>
                                    ) : recommendations.length > 0 ? (
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-60 overflow-y-auto p-1">
                                            {recommendations.map((book) => (
                                                <div key={book.id || book.book_id} className="border rounded-md p-3 hover:bg-gray-50 transition-colors flex flex-col justify-between">
                                                    <div>
                                                        <h4 className="font-semibold text-sm text-gray-800 line-clamp-2">{book.title}</h4>
                                                        <p className="text-xs text-gray-600 mt-1">{book.author}</p>
                                                    </div>
                                                    <div className="mt-2 flex items-center text-xs text-gray-500">
                                                        <Book className="mr-1 w-3 h-3" /> {book.department}
                                                        <span className="ml-auto bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
                                                            {book.rating || '4.0'} ★
                                                        </span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="text-center py-6 text-gray-500 bg-gray-50 rounded-lg">
                                            <p>No specific recommendations found for this title.</p>
                                        </div>
                                    )}
                                </div>

                            </div>
                        </div>
                    </div>

                    <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                        <button
                            type="button"
                            className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                            onClick={onClose}
                        >
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RecommendationModal;
