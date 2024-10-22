import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { IoLogoLinkedin } from 'react-icons/io';
import './RoleProfileFetcher.css';

const RoleProfileFetcher = () => {
    const [role, setRole] = useState(localStorage.getItem('role') || '');
    const [companyName, setCompanyName] = useState(localStorage.getItem('companyName') || '');
    const [profiles, setProfiles] = useState(JSON.parse(localStorage.getItem('profiles')) || []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('http://localhost:8006/scrape_role_profiles', {
                role,
                company_name: companyName,
            });
            setProfiles(response.data);
            localStorage.setItem('profiles', JSON.stringify(response.data)); // Save profiles to localStorage
        } catch (error) {
            console.error("Error fetching profiles:", error);
        }
    };

    // Save role and company name in localStorage
    useEffect(() => {
        localStorage.setItem('role', role);
        localStorage.setItem('companyName', companyName);
    }, [role, companyName]);

    return (
        <div className="role-profile-fetcher">
            <h1 className="role-profile-fetcher__heading">Role Profile Fetcher</h1>
            <form className="role-profile-fetcher__form" onSubmit={handleSubmit}>
                <input 
                    type="text" 
                    placeholder="Enter Role" 
                    value={role} 
                    onChange={(e) => setRole(e.target.value)} 
                    required 
                    className="role-profile-fetcher__input"
                />
                <input 
                    type="text" 
                    placeholder="Enter Company Name" 
                    value={companyName} 
                    onChange={(e) => setCompanyName(e.target.value)} 
                    required 
                    className="role-profile-fetcher__input"
                />
                <button type="submit" className="role-profile-fetcher__button">Fetch Profiles</button>
            </form>

            <div>
                {profiles.length > 0 && (
                    <ul className="role-profile-fetcher__profiles">
                        {profiles.map((profile, index) => (
                            <li key={index} className="role-profile-fetcher__profile">
                                <h3>{profile.name}</h3>
                                <a href={profile.linkedin_url} target="_blank" rel="noopener noreferrer">
                                    <IoLogoLinkedin /> LinkedIn Profile
                                </a>
                                <p>{profile.about_section}</p>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
};

export default RoleProfileFetcher;