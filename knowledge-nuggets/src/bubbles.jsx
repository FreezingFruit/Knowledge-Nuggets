import React from "react";
import "./Bubbles.css";

const Bubbles = () => {
  const bubbleData = [
    15, 12, 91, 24, 41, 34, 21, 32, 21, 71, 16, 81, 23, 16, 12, 37, 26, 36, 42,
    16, 26, 35, 56, 24, 26, 18, 51, 36, 73, 25, 15, 12, 99, 24, 20, 34, 26, 32, 27,
    74, 16, 97, 23, 16, 12, 32, 26, 21, 41, 16, 21, 31, 51, 21, 21, 18, 51, 31, 71, 21
  ];

  return (
    <div className="bubble-container">
      <div className="bubbles">
        {bubbleData.map((i, index) => (
          <span key={index} style={{ "--i": i }}></span>
        ))}
      </div>
    </div>
  );
};

export default Bubbles;
