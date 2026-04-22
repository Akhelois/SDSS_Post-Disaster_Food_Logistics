import React from "react";
import { LuRadar, LuTriangleAlert } from "react-icons/lu";
import "../styles/SidebarHeader.css";

export default function SidebarHeader({ disasterInfo }) {
  return (
    <div className="header">
      <div className="header-content">
        <div className="header-icon">
          <LuRadar className="radar-icon" />
        </div>
        <div className="header-text">
          <h1>SDSS Logistik Bencana</h1>
          <p>Real-time Damage Assessment &amp; Automated Routing</p>
        </div>
      </div>
      {disasterInfo && disasterInfo.summary && (
        <div className="disaster-badge">
          <LuTriangleAlert size={14} className="alert-icon" />
          <span>{disasterInfo.summary}</span>
        </div>
      )}
    </div>
  );
}
