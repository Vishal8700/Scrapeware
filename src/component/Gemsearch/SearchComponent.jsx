import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FaSearch, FaLink, FaMapMarkerAlt, FaCalendarAlt, FaBuilding } from 'react-icons/fa';
import './SearchComponent.css';

const SearchComponent = () => {
  const [keyword, setKeyword] = useState(localStorage.getItem('keyword') || '');
  const [auctions, setAuctions] = useState(JSON.parse(localStorage.getItem('auctions')) || []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Save keyword and auctions to localStorage whenever they change
    localStorage.setItem('keyword', keyword);
    localStorage.setItem('auctions', JSON.stringify(auctions));
  }, [keyword, auctions]);

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('http://localhost:5000/scrape-auctions/', { keyword, page: 1 });
      if (response.data.status === 'success') {
        setAuctions(response.data.data);
        if (response.data.data.length === 0) {
          setError('No auctions found.');
        }
      } else {
        setError('Failed to fetch auctions.');
      }
    } catch (error) {
      console.error('Error fetching auctions:', error);
      setError('An error occurred while fetching auctions.');
    }
    setLoading(false);
  };

  return (
    <div className="search-component">
      <div className="search-bar">
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="Enter keyword to search auctions"
        />
        <button onClick={handleSearch} disabled={loading}>
          {loading ? 'Searching...' : <FaSearch />}
        </button>
      </div>
      {error && <div className="error-message">{error}</div>}
      <div className="auction-list">
        {auctions.map((auction, index) => (
          <div key={index} className="auction-item">
            <h3>{auction['Auction ID']}</h3>
            <p>{auction['Brief']}</p>
            <div className="auction-details">
              <p><FaMapMarkerAlt /> {auction['Location']}</p>
              <p><FaCalendarAlt /> Start: {auction['Start Date']}</p>
              <p><FaCalendarAlt /> End: {auction['End Date']}</p>
              <p><FaBuilding /> {auction['Organizer']}</p>
              <a href={auction['Link']} target="_blank" rel="noopener noreferrer">
                <FaLink /> View Auction
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchComponent;
