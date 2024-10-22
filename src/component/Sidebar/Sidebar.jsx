import React from 'react';
import './Sidebar.css';
import { FaHeart } from 'react-icons/fa';
import logo from './logo.png'
const Sidebar = ({ onItemClick }) => {
  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <img src={logo} alt="Logo" />
      </div>
      <div className="sidebar-buttons">
        <button onClick={() => onItemClick('search')}>Auctions</button>
        <button onClick={() => onItemClick('option2')}>Bids</button>
        <button onClick={() => onItemClick('option3')}>Company Search</button>
        <button onClick={() => onItemClick('option4')}>Company Details</button>
        <button onClick={() => onItemClick('option5')}>Check Roles</button>
      </div>
      <div className="sidebar-footer">
        <p>Made with <FaHeart className="heart-icon" /> by keshav & git_alien</p>
      </div>
    </div>
  );
};

export default Sidebar;