import React from 'react';
import '../styles/LoadingSkeleton.css';

export default function LoadingSkeleton() {
  return (
    <>
      {/* Metric skeletons */}
      <div className="metrics-row" id="metrics-section">
        <div className="metric-card skeleton-card">
          <div className="skeleton-circle" />
          <div className="skeleton-text-group">
            <div className="skeleton-line short" />
            <div className="skeleton-line medium" />
            <div className="skeleton-line tiny" />
          </div>
        </div>
        <div className="metric-card skeleton-card">
          <div className="skeleton-circle" />
          <div className="skeleton-text-group">
            <div className="skeleton-line short" />
            <div className="skeleton-line medium" />
            <div className="skeleton-line tiny" />
          </div>
        </div>
      </div>

      {/* Map skeleton */}
      <div className="map-section skeleton-map-section">
        <div className="map-toolbar">
          <div className="skeleton-line long" />
        </div>
        <div className="map-container skeleton-map-body">
          <div className="skeleton-pulse-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="10" r="3"/>
              <path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/>
            </svg>
            <span>Memuat peta bencana...</span>
          </div>
        </div>
      </div>

      {/* Table skeleton */}
      <div className="table-section">
        <div className="table-header">
          <div className="skeleton-line long" />
        </div>
        <div className="skeleton-table-body">
          {[...Array(4)].map((_, i) => (
            <div className="skeleton-table-row" key={i}>
              <div className="skeleton-line short" />
              <div className="skeleton-line medium" />
              <div className="skeleton-line short" />
              <div className="skeleton-line medium" />
              <div className="skeleton-line short" />
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
