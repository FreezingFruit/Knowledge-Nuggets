import React, { useEffect, useState } from "react";
import "./Profile.css";
import Navbar from "./Navbar";
import { auth, db, ref, onValue } from "./firebase/firebase";
import { onAuthStateChanged } from "firebase/auth";

const Profile = () => {
  const [userEmail, setUserEmail] = useState("Loading...");
  const [selectedSummary, setSelectedSummary] = useState(null);
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const unsubscribeAuth = onAuthStateChanged(auth, (user) => {
      if (user) {
        setUserEmail(user.email);
        // Fetch summaries when user is logged in
        const summariesRef = ref(db, `summaries/${user.uid}`);
        onValue(summariesRef, (snapshot) => {
          const data = snapshot.val();
          const loadedSummaries = data
            ? Object.entries(data).map(([id, value]) => ({
                id,
                ...value,
              }))
            : [];
          setSummaries(loadedSummaries);
          setLoading(false);
        });
      } else {
        setUserEmail("No user logged in");
        setLoading(false);
      }
    });

    return () => unsubscribeAuth();
  }, []);

  const handleSummaryClick = (summary) => {
    setSelectedSummary(summary);
    setMenuOpen(false);
  };

  return (
    <>
      <Navbar />
      <div className="profile-container">
        <div className={`profile-left ${menuOpen ? "open" : ""}`}>
          <h3>Summary History</h3>
          {loading ? (
            <p>Loading summaries...</p>
          ) : summaries.length === 0 ? (
            <p>No summaries found</p>
          ) : (
            <ul className="summary-list">
              {summaries.map((summary) => (
                <li
                  key={summary.id}
                  onClick={() => handleSummaryClick(summary)}
                >
                  <div className="summary-item">
                    <div className="summary-meta">
                      <span className="summary-type">{summary.type}</span>
                      <span className="summary-date">
                        {new Date(summary.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="summary-preview">
                      {summary.content.substring(0, 50)}...
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="profile-right">
          <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)}>
            ☰
          </button>
          {selectedSummary ? (
            <>
              <h2>{selectedSummary.type} Summary</h2>
              <div className="summary-meta">
                <p>
                  Video URL:{" "}
                  <a
                    href={selectedSummary.videoUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {selectedSummary.videoUrl}
                  </a>
                </p>
                <p>
                  Created:{" "}
                  {new Date(selectedSummary.timestamp).toLocaleString()}
                </p>
              </div>
              <div className="summary-content">
                <h3>Narrative Summary</h3>
                <p>{selectedSummary.content}</p>
                <h3>Visual Elements</h3>
              </div>
            </>
          ) : (
            <p>Select a summary from the list to view details</p>
          )}
        </div>
      </div>
    </>
  );
};

export default Profile;
