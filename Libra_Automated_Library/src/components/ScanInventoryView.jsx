import { useState, useEffect } from 'react';
import { getLastNfcScan, getBookByNfcId } from '../utils/api';
import { useNotification } from '../hooks/useNotifications';
import { Radio, X, Download } from 'lucide-react';
import { formatDate } from '../utils/helpers';

const ScanInventoryView = () => {
  const { addNotification } = useNotification();
  const [isScanning, setIsScanning] = useState(false);
  const [scannedBooks, setScannedBooks] = useState([]);
  const [loading, setLoading] = useState(false);

  // Poll for NFC scans
  useEffect(() => {
    if (!isScanning) return;

    const interval = setInterval(async () => {
      try {
        const res = await getLastNfcScan();
        if (res && res.nfc_tag_id) {
          // Check if already scanned
          const alreadyScanned = scannedBooks.some(b => b.nfc_tag_id === res.nfc_tag_id);
          if (!alreadyScanned) {
            // Fetch book details by NFC ID
            const bookData = await getBookByNfcId(res.nfc_tag_id);
            if (bookData) {
              setScannedBooks(prev => [
                {
                  ...bookData,
                  nfc_tag_id: res.nfc_tag_id,
                  scanned_at: new Date().toISOString()
                },
                ...prev
              ]);
              addNotification(`📚 Book scanned: ${bookData.title}`, 'success');
            } else {
              addNotification(`NFC: ${res.nfc_tag_id} - Book not found in database`, 'warning');
              setScannedBooks(prev => [
                {
                  id: null,
                  title: 'Unknown Book',
                  author: 'N/A',
                  nfc_tag_id: res.nfc_tag_id,
                  scanned_at: new Date().toISOString(),
                  unknown: true
                },
                ...prev
              ]);
            }
          }
        }
      } catch (error) {
        console.error('NFC scan error:', error);
      }
    }, 1000); // Poll every 1 second

    return () => clearInterval(interval);
  }, [isScanning, scannedBooks]);

  const handleClear = () => {
    setScannedBooks([]);
    addNotification('Scan history cleared', 'info');
  };

  const handleRemoveScan = (nfcId) => {
    setScannedBooks(prev => prev.filter(b => b.nfc_tag_id !== nfcId));
  };

  const handleExport = () => {
    const csv = [
      ['Title', 'Author', 'NFC ID', 'Scanned At'],
      ...scannedBooks
        .filter(b => !b.unknown)
        .map(b => [b.title, b.author, b.nfc_tag_id, formatDate(b.scanned_at)])
    ]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `inventory-scan-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    addNotification('Inventory exported as CSV', 'success');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Radio className="w-6 h-6 text-blue-600" />
          <h2 className="text-lg sm:text-xl font-medium font-['Poppins'] text-gray-600 tracking-tight">
            Scan Inventory
          </h2>
        </div>
        <p className="text-gray-500 text-sm">Tap NFC cards to scan and log book inventory</p>
      </div>

      {/* Scan Controls */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
        <div className="flex flex-wrap items-center gap-3 sm:gap-4">
          <button
            onClick={() => setIsScanning(!isScanning)}
            className={`px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg font-semibold flex items-center gap-2 transition-all ${
              isScanning
                ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            <Radio className={`w-5 h-5 ${isScanning ? 'animate-spin' : ''}`} />
            {isScanning ? 'Stop Scanning' : 'Start Scanning'}
          </button>

          {scannedBooks.length > 0 && (
            <>
              <button
                onClick={handleExport}
                className="px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg font-semibold flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white transition-all"
              >
                <Download className="w-5 h-5" />
                Export CSV
              </button>
              <button
                onClick={handleClear}
                className="px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg font-semibold bg-gray-300 hover:bg-gray-400 text-gray-800 transition-all"
              >
                Clear All
              </button>
            </>
          )}
        </div>

        <div className="text-sm text-gray-600">
          {isScanning ? (
            <span className="flex items-center gap-2 text-blue-600 font-medium">
              <span className="inline-block w-2 h-2 bg-blue-600 rounded-full animate-pulse"></span>
              Listening for NFC scans...
            </span>
          ) : (
            <span className="text-gray-500">Click "Start Scanning" to begin scanning NFC cards</span>
          )}
        </div>
      </div>

      {/* Scanned Books Summary */}
      {scannedBooks.length > 0 && (
        <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
          <p className="text-sm font-semibold text-blue-900">
            📊 Total Scans: <span className="text-lg">{scannedBooks.length}</span>
          </p>
          <p className="text-xs text-blue-700 mt-1">
            Valid Books: {scannedBooks.filter(b => !b.unknown).length} | Unknown: {scannedBooks.filter(b => b.unknown).length}
          </p>
        </div>
      )}

      {/* Scanned Books Table */}
      {scannedBooks.length > 0 ? (
        <div className="overflow-x-auto bg-white rounded-xl shadow-sm border border-gray-100">
          <table className="min-w-[760px] w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Book Title
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Author
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  NFC ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Scanned At
                </th>
                <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {scannedBooks.map((book, index) => (
                <tr key={`${book.nfc_tag_id}-${index}`} className={`hover:bg-blue-50 ${book.unknown ? 'bg-red-50' : ''}`}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {book.title}
                      {book.unknown && <span className="text-xs text-red-600 ml-2">(Not in DB)</span>}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {book.author}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                    {book.nfc_tag_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatDate(book.scanned_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <button
                      onClick={() => handleRemoveScan(book.nfc_tag_id)}
                      className="inline-flex items-center justify-center p-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                      title="Remove from scan list"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-100">
          <Radio className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 font-medium mb-2">No books scanned yet</p>
          <p className="text-gray-400 text-sm">Click "Start Scanning" and tap NFC cards on the reader</p>
        </div>
      )}
    </div>
  );
};

export default ScanInventoryView;
