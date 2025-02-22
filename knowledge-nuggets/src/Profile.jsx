import React, { useEffect, useState } from "react";
import "./Profile.css";
import Navbar from "./Navbar";
import { auth } from "./firebase/firebase"; // Import Firebase auth
import { onAuthStateChanged } from "firebase/auth";

const Profile = () => {
  const [userEmail, setUserEmail] = useState("Loading...");
  const [selectedSummary, setSelectedSummary] = useState(
    "Select a summary from the list."
  );

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        setUserEmail(user.email);
      } else {
        setUserEmail("No user logged in");
      }
    });

    return () => unsubscribe();
  }, []);

  const summaries = [
    "This is summary 1",
    "This is summary 2",
    "This is summary 3",
    "This is summary 4",
  ];

  const handleSummaryClick = (index) => {
    setSelectedSummary(summaries[index]);
  };

  return (
    <>
      <Navbar />
      <div className="profile-container">
        <div className="profile-left">
          <h3>Summary List</h3>
          <ul className="summary-list">
            {summaries.map((summary, index) => (
              <li key={index} onClick={() => handleSummaryClick(index)}>
                Summary {index + 1}
              </li>
            ))}
          </ul>
        </div>
        <div className="profile-right">
          <h2>Summary</h2>
          <p>{selectedSummary}</p>
        </div>
      </div>
    </>
  );
};

export default Profile;
