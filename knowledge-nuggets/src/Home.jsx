import React, { useState } from "react";
import { Link } from "react-router-dom";
import "./Home.css";
import Navbar from "./Navbar";
import Bubbles from "./bubbles";

const Home = () => {
  const [url, setUrl] = useState("");
  const [submittedUrl, setSubmittedUrl] = useState("");
  const [summaryText, setSummaryText] = useState("");
  const [urlError, setUrlError] = useState("");
  const [loading, setLoading] = useState(false);

  // Regex for YouTube URL validation
  const youtubeRegex =
    /^(https?:\/\/)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)\/(watch\?v=[a-zA-Z0-9_-]{11}(&.*)?|.+\/videos\/[a-zA-Z0-9_-]{11})$/;

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate the URL with the regex
    if (!youtubeRegex.test(url)) {
      setUrlError("Invalid YouTube URL. Please enter a valid link.");
      return;
    }

    setUrlError("");
    setSubmittedUrl(url);
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/analyze-video", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ video_url: url }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Format the summary text
      const summary = [
        data.youtube_captions && `YouTube Captions: ${data.youtube_captions}`,
        data.transcription && `Transcription: ${data.transcription}`,
        data.scene_frequency && "Visual Content Analysis:",
        data.scene_frequency &&
          Object.entries(data.scene_frequency)
            .map(([content, count]) => `• ${content}: ${count} occurrences`)
            .join("\n"),
      ]
        .filter(Boolean)
        .join("\n\n");

      setSummaryText(summary);
    } catch (error) {
      console.error("Error:", error);
      setUrlError("Error analyzing video. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />

      <div className="container">
        <div className="form-container">
          <h1>Enter Video URL</h1>
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Enter Video Link"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={loading}
            />
            <button type="submit" disabled={loading}>
              {loading ? "Analyzing..." : "Generate Summary"}
            </button>
          </form>

          {urlError && <p className="error">{urlError}</p>}

          <div className="result">
            {submittedUrl && !loading && (
              <>
                <h2>Analyzed URL:</h2>
                <p>{submittedUrl}</p>
              </>
            )}
          </div>
        </div>

        {summaryText && !loading && (
          <div className="summary-container">
            <h2>Analysis Results</h2>
            <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
              {summaryText}
            </pre>
          </div>
        )}

        {loading && (
          <div className="summary-container">
            <h2>Analyzing video...</h2>
            <p>This may take a few minutes depending on the video length.</p>
          </div>
        )}
      </div>

      <div className="how-to-container">
        <h1>How to Use the Knowledge Nuggets?</h1>
        <h2>You can easily summarize videos with just 3 simple steps</h2>
        <div className="how-to">
          <p>Step 1: Copy and Paste the Video Link.</p>
        </div>

        <div className="how-to">
          <p>Step 2: Click Generate Summary.</p>
        </div>

        <div className="how-to">
          <p>
            Step 3: Read your generated summary to increase learning efficiency.
          </p>
        </div>
      </div>
    </>
  );
};

export default Home;
