
import { Search, ChevronLeft, ChevronRight, Building2, Package, Calendar, FileText } from 'lucide-react';
import './Bidsearch.css';

export default function Bidsearch({
  searchQuery, setSearchQuery,
  bids, setBids,
  currentPage, setCurrentPage,
  loading, setLoading,
  error, setError
}) {
  const itemsPerPage = 10;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentBids = bids.slice(startIndex, endIndex);

  const fetchBids = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ search_text: searchQuery }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch bids');
      }

      const data = await response.json();
      setBids(data.results);  // Ensure you use the correct response field
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (searchQuery) {
      fetchBids();
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(prev => prev - 1);
    }
  };

  const handleNextPage = () => {
    if (endIndex < bids.length) {
      setCurrentPage(prev => prev + 1);
    }
  };

  return (
    <div className="search-sidebar">
      <div className="search-container">
        <Search className="search-icon" />
        <input
          type="text"
          placeholder="Search bids..."
          className="search-input"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button className="search-button" onClick={handleSearch}>Search</button>
      </div>

      {loading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Fetching bids, please wait...</p>
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {!loading && !error && currentBids.length === 0 && searchQuery && (
        <div className="no-results">
          <p>No bids found for "{searchQuery}".</p>
        </div>
      )}

      <div className="bids-container">
        {currentBids.map((bid) => (
          <div key={bid.bid_number} className="bid-card">
            <div className="bid-card-content">
              <div className="bid-header">
                <FileText className="bid-icon" />
                <div className="bid-info">
                  <h3 className="bid-number">
                    <a href={bid.link} target="_blank" rel="noopener noreferrer" className="bid-number-link">
                      {bid.bid_number}
                    </a>
                  </h3>
                  <p className="bid-items">{bid.items}</p>

                  <div className="bid-detail">
                    <Building2 className="detail-icon" />
                    <span>{bid.department}</span>
                  </div>

                  <div className="bid-detail">
                    <Package className="detail-icon" />
                    <span>{bid.quantity}</span>
                  </div>

                  <div className="bid-detail">
                    <Calendar className="detail-icon" />
                    <span>{bid.start_date} - {bid.end_date}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="pagination">
        <button
          className="pagination-button"
          onClick={handlePrevPage}
          disabled={currentPage === 1}
        >
          <ChevronLeft className="button-icon" />
          Previous
        </button>

        <span className="page-info">
          Page {currentPage} of {Math.ceil(bids.length / itemsPerPage)}
        </span>

        <button
          className="pagination-button"
          onClick={handleNextPage}
          disabled={endIndex >= bids.length}
        >
          Next
          <ChevronRight className="button-icon" />
        </button>
      </div>
    </div>
  );
}
