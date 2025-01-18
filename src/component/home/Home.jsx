import React, { useState, useEffect } from 'react';
import Sidebar from '../Sidebar/Sidebar';
import SearchComponent from '../Gemsearch/SearchComponent';
import './Home.css';
import Bidsearch from '../Bidsearch/Bidsearch';
import CompanySearch from '../Companysearch/Companysearch';
import CompanyDetail from '../CompanyDetails/CompanyDetails';
import RoleProfileFetcher from '../Rolesearch/Rolesearch';

const Home = () => {
  const [activeComponent, setActiveComponent] = useState(localStorage.getItem('activeComponent') || null);

  // State for CompanySearch
  const [keywords, setKeywords] = useState(localStorage.getItem('keywords') || '');
  const [location, setLocation] = useState(localStorage.getItem('location') || '');
  const [companies, setCompanies] = useState(JSON.parse(localStorage.getItem('companies')) || []);

  // State for CompanyDetail
  const [companyDetails, setCompanyDetails] = useState(null);
  const [url, setUrl] = useState('');

  // State for Bidsearch
  const [searchQuery, setSearchQuery] = useState('');
  const [bids, setBids] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSidebarClick = (component) => {
    setActiveComponent(component);
    localStorage.setItem('activeComponent', component); // Save active component in localStorage
  };

  // Persist company search-related state in localStorage
  useEffect(() => {
    localStorage.setItem('keywords', keywords);
    localStorage.setItem('location', location);
    localStorage.setItem('companies', JSON.stringify(companies));
  }, [keywords, location, companies]);

  return (
    <div className="home-container">
      <Sidebar onItemClick={handleSidebarClick} />
      
      <div className="content-area">
        {activeComponent === 'search' && <SearchComponent />}
        {activeComponent === 'option2' && (
          <Bidsearch
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            bids={bids}
            setBids={setBids}
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            loading={loading}
            setLoading={setLoading}
            error={error}
            setError={setError}
          />
        )}
        {activeComponent === 'option3' && (
          <CompanySearch
            keywords={keywords}
            setKeywords={setKeywords}
            location={location}
            setLocation={setLocation}
            companies={companies}
            setCompanies={setCompanies}
          />
        )}
        {activeComponent === 'option4' && (
          <CompanyDetail
            companyDetails={companyDetails}
            setCompanyDetails={setCompanyDetails}
            url={url}
            setUrl={setUrl}
          />
        )}

        {activeComponent === 'option5' && (
          <RoleProfileFetcher/>)}
      </div>
    </div>
  );
};

export default Home;
