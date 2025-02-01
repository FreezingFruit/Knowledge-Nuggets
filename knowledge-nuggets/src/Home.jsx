import React, { useState } from "react";
import "./Home.css";
import Navbar from "./Navbar";
import Bubbles from "./bubbles";

const Home = () => {
  const [url, setUrl] = useState("");
  const [submittedUrl, setSubmittedUrl] = useState("");
  const [summaryText, setSummaryText] = useState("");
  const [urlError, setUrlError] = useState(""); // Error state for URL

  // Regex for YouTube URL validation
  const youtubeRegex =
    /^(https?:\/\/)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)\/(watch\?v=[a-zA-Z0-9_-]{11}(&.*)?|.+\/videos\/[a-zA-Z0-9_-]{11})$/;

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validate the URL with the regex
    if (!youtubeRegex.test(url)) {
      setUrlError("Invalid YouTube URL. Please enter a valid link.");
      return; // Stop further execution if URL is invalid
    }

    setUrlError(""); // Clear error if URL is valid
    setSubmittedUrl(url); // Update the submitted URL

    // Example of setting summary text
    const newSummary =
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit.";
    setSummaryText(newSummary);

    console.log("URL Submitted:", url);
    console.log("Summary Text:", newSummary);
  };

  return (
    <>
      <Navbar />
      <Bubbles />

      <div className="container">
        <div className="form-container">
          <h1>Enter YouTube URL</h1>
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Enter YouTube Link"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <button type="submit">Submit</button>
          </form>

          {/* Display the error message if URL is invalid */}
          {urlError && <p className="error">{urlError}</p>}

          <div className="result">
            {submittedUrl && (
              <>
                <h2>You entered:</h2>
                <p>{submittedUrl}</p>
              </>
            )}
          </div>
        </div>

        {/* Conditionally render the summary section */}
        {summaryText && (
          <div className="summary-container">
            <h2>Summary</h2>
            <p>{summaryText}</p>
          </div>
        )}
      </div>
    </>
  );
};

export default Home;
