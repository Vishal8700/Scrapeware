import { useState } from 'react';
import { Search } from 'lucide-react';
import './CompanySearch.css';

export default function CompanySearch({ keywords, setKeywords, location, setLocation, companies, setCompanies }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8002/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          keywords: keywords || "UAV, drone, quadcopter", // Use the state value for keywords
          location: location || "America" // Use the state value for location
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Error:", errorData);
        throw new Error('Failed to fetch data');
      }

      const data = await response.json();
      console.log(data); // Inspect this output

      if (Array.isArray(data.companies)) {
        setCompanies(data.companies);
      } else {
        console.error("Expected an array but got:", data.companies);
        setCompanies([]); // Set to empty array or handle accordingly
      }
    } catch (error) {
      console.error("Request failed:", error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="CompanySearch-container">
  <div className="CompanySearch-input-container">
    <input
      type="text"
      placeholder="Enter keywords (comma separated)"
      className="CompanySearch-input"
      value={keywords} // Use the prop value
      onChange={(e) => setKeywords(e.target.value)} // Update parent state for keywords
    />
    <input
      type="text"
      placeholder="Enter location"
      className="CompanySearch-input"
      value={location} // Use the prop value
      onChange={(e) => setLocation(e.target.value)} // Update parent state for location
    />
    <button onClick={handleSearch} className="CompanySearch-button">
      <Search /> Search
    </button>
  </div>



      {loading && <p className="loading-message">Loading...</p>}
      {error && <p className="error-message">{error}</p>}

      <div className="companies-list-container">
        {Array.isArray(companies) && companies.map((company, index) => (
          <div key={index} className="company-card">
            <h3 className="company-title">{company.title}</h3>
            <p className="company-snippet">{company.snippet}</p>
            <a href={company.link} target="_blank" rel="noopener noreferrer" className="company-link">
              {company.link}
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}
