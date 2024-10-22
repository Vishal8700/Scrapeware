import { useState, useEffect } from 'react';
import { FaGlobe, FaIndustry, FaUsers, FaHome, FaCalendar, FaStar } from 'react-icons/fa';
import './CompanyDetail.css';

export default function CompanyDetail({ companyDetails, setCompanyDetails, url, setUrl }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load previously fetched company details from localStorage
  useEffect(() => {
    const savedDetails = localStorage.getItem('companyDetails');
    if (savedDetails) {
      setCompanyDetails(JSON.parse(savedDetails));
    }
  }, [setCompanyDetails]);

  const handleFetchDetails = async () => {
    setLoading(true);
    setError(null);

    try {
      // Validate URL
      if (!url) {
        throw new Error('Please enter a valid URL.');
      }

      const response = await fetch('http://localhost:8003/scrape-company/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ company_url: url }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Error:", errorData);
        throw new Error('Failed to fetch company details');
      }

      const data = await response.json();
      setCompanyDetails(data); // Store company details in parent state
      localStorage.setItem('companyDetails', JSON.stringify(data)); // Save to localStorage
    } catch (error) {
      console.error("Failed to fetch company details:", error);
      setError(error.message); // Set error message
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="company-search-container">
      {/* Input Field for URL */}
      <input
        type="text"
        placeholder="Enter company URL"
        value={url}
        onChange={(e) => setUrl(e.target.value)} // Update parent state for URL
        className="company-search-input"
      />
      {/* Fetch Button */}
      <button onClick={handleFetchDetails} className="company-search-button">
        Fetch Details
      </button>

      {/* Loading and Error Messages */}
      {loading && <p>Loading...</p>}
      {error && (
        <p style={{ color: 'red' }}>{error}</p>
      )}

      {/* Display Company Details */}
      {companyDetails && (
        <div className="company-details-container">
          <h1>Company Details</h1>
          <div className="company-details-scroll">
            <div className="section">
              <div className="section-title">Company URL:</div>
              <div className="section-content">
                <a href={url} target="_blank" rel="noreferrer" className="url">{url}</a>
              </div>
            </div>

            {companyDetails.overview && (
              <div className="section">
                <div className="section-title">Overview:</div>
                <div className="section-content">{companyDetails.overview}</div>
              </div>
            )}

            {companyDetails.website && (
              <div className="section">
                <div className="section-title">Website:</div>
                <div className="section-content">
                  <FaGlobe /> <a href={companyDetails.website} target="_blank" rel="noreferrer" className="url">{companyDetails.website}</a>
                </div>
              </div>
            )}

            {companyDetails.industry && (
              <div className="section">
                <div className="section-title">Industry:</div>
                <div className="section-content"><FaIndustry /> {companyDetails.industry}</div>
              </div>
            )}

            {companyDetails.company_size && (
              <div className="section">
                <div className="section-title">Company Size:</div>
                <div className="section-content"><FaUsers /> {companyDetails.company_size}</div>
              </div>
            )}

            {companyDetails.headquarters && (
              <div className="section">
                <div className="section-title">Headquarters:</div>
                <div className="section-content"><FaHome /> {companyDetails.headquarters}</div>
              </div>
            )}

            {companyDetails.founded && (
              <div className="section">
                <div className="section-title">Founded:</div>
                <div className="section-content"><FaCalendar /> {companyDetails.founded}</div>
              </div>
            )}

            {companyDetails.specialties && (
              <div className="section">
                <div className="section-title">Specialties:</div>
                <div className="section-content"><FaStar /> {companyDetails.specialties}</div>
              </div>
            )}

            {companyDetails.top_posts && companyDetails.top_posts.length > 0 && (
              <div className="section">
                <div className="section-title">Recent Posts:</div>
                <ul className="top-posts-list">
                  {companyDetails.top_posts.map((post, index) => (
                    <li key={index}>{post}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}