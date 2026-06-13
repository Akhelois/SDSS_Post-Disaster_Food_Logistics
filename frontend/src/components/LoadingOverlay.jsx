import React from 'react';
import { LuRadar } from 'react-icons/lu';

export default function LoadingOverlay() {
  return (
    <div className="loading-overlay">
      <div className="loading-content">
        <div className="loading-icon">
          <LuRadar />
        </div>
        <div className="loader"></div>
        <div className="loading-text">
          <strong>Menganalisis Citra Satelit</strong>
          Menghitung rute distribusi bantuan...
        </div>
      </div>
    </div>
  );
}
