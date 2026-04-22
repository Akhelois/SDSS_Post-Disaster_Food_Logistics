import React, { useState, useEffect } from "react";
import { LuMenu, LuClock } from "react-icons/lu";
import "../styles/TopNavBar.css";

export default function TopNavBar({ onMenuClick }) {
  const [currentDateTime, setCurrentDateTime] = useState(new Date());

  // Update clock every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentDateTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatDateTime = (date) => {
    const options = {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    };
    return date.toLocaleDateString("en-US", options);
  };

  return (
    <div className="top-nav-bar">
      <div className="nav-left">
        <button className="menu-btn" onClick={onMenuClick} title="Toggle Menu">
          <LuMenu size={20} />
        </button>
        <div className="nav-logo">
          <span className="logo-text">SDSS Dashboard</span>
        </div>
      </div>

      <div className="nav-right">
        <div className="datetime-display">
          <LuClock size={16} />
          <span>{formatDateTime(currentDateTime)}</span>
        </div>
      </div>
    </div>
  );
}
