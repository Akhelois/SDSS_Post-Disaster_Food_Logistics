import React from 'react';
import { TbLoader2 } from 'react-icons/tb';
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
            <TbLoader2 style={{ fontSize: '38px', color: 'var(--p-main, #DC2626)', animation: 'clean-spin 1s linear infinite' }} />
            <span style={{ marginTop: '10px' }}>Memuat data spasial bencana...</span>
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
