// Navbar.jsx
import React from "react";
import { Link } from "react-router-dom";
import "./Navbar.css";

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-title">
        <h1>Knowledge Nuggets</h1>
      </div>
      <div className="navbar-links">
        <Link to="/login" className="sign-in-button">
          Sign In
        </Link>
      </div>
    </nav>
  );
};

export default Navbar;
