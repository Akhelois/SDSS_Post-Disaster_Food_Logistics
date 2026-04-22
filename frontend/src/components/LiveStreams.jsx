import React, { useState } from "react";
import "../styles/LiveStreams.css";

export default function LiveStreams() {
  const [activeStream, setActiveStream] = useState(null);

  const liveStreams = [
    {
      id: 1,
      name: "KompasTV",
      region: "Indonesia",
      type: "YouTube Live",
      status: "LIVE",
      url: "https://www.youtube.com/embed/DOOrIxw5xOw",
    },
    {
      id: 2,
      name: "Metro TV",
      region: "Indonesia",
      type: "YouTube Live",
      status: "LIVE",
      url: "https://www.youtube.com/embed/AUE5iHINUIw",
    },
    // {
    //   id: 3,
    //   name: "TV One",
    //   region: "Indonesia",
    //   type: "YouTube Live",
    //   status: "LIVE",
    //   url: "https://www.youtube.com/embed/AUE5iHINUIw",
    // },
  ];

  const currentStream = activeStream || liveStreams[0];

  return (
    <div className="live-streams">
      <div className="video-section">
        <div className="video-header">
          <h3>{currentStream.name}</h3>
        </div>
        <div className="inline-video-player">
          <iframe
            width="100%"
            height="100%"
            src={currentStream.url + "?autoplay=1"}
            title={currentStream.name}
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          ></iframe>
        </div>
      </div>

      <div className="channels-switcher">
        <div className="switcher-header">
          <span className="channel-label">Channels</span>
          <span className="channel-count">
            {liveStreams.filter((s) => s.status === "LIVE").length}/
            {liveStreams.length}
          </span>
        </div>
        <div className="channels-list">
          {liveStreams.map((stream) => (
            <button
              key={stream.id}
              className={`channel-btn ${currentStream.id === stream.id ? "active" : ""}`}
              onClick={() => setActiveStream(stream)}
            >
              <span className="channel-name">{stream.name}</span>
              <span className={`channel-status ${stream.status.toLowerCase()}`}>
                ● {stream.status}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
