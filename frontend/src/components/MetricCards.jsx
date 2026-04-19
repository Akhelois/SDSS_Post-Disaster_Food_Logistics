import React from 'react';
import { LuMap, LuTriangleAlert, LuUsers, LuWarehouse } from 'react-icons/lu';
import '../styles/MetricCards.css';

export default function MetricCards({ metrics }) {
  return (
    <div className="metrics-card">
      <div className="metrics-grid">
        <div className="metric">
          <div className="metric-icon highlight">
            <LuMap />
          </div>
          <div className="metric-info">
            <span className="metric-title">Wilayah Aktif</span>
            <span className="metric-value highlight">{metrics?.active_areas || 0}</span>
          </div>
        </div>
        <div className="metric">
          <div className="metric-icon danger">
            <LuTriangleAlert />
          </div>
          <div className="metric-info">
            <span className="metric-title">Titik Kerusakan</span>
            <span className="metric-value danger">{metrics?.total_damage || 0}</span>
          </div>
        </div>
        <div className="metric">
          <div className="metric-icon neutral">
            <LuUsers />
          </div>
          <div className="metric-info">
            <span className="metric-title">Est. Terdampak</span>
            <span className="metric-value">{metrics?.estimated_impacts || 0} Jiwa</span>
          </div>
        </div>
        <div className="metric">
          <div className="metric-icon success">
            <LuWarehouse />
          </div>
          <div className="metric-info">
            <span className="metric-title">Posko Hub Aktif</span>
            <span className="metric-value success">{metrics?.total_hubs || 0} Unit</span>
          </div>
        </div>
      </div>
    </div>
  );
}
