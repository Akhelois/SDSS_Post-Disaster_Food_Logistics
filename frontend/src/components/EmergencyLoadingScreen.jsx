import React, { useState, useEffect } from 'react';
import { TbLoader2, TbMap2, TbDatabase, TbSatellite, TbUsers, TbShieldCheck } from 'react-icons/tb';
import '../styles/EmergencyLoading.css';

const LOADING_STEPS = [
  'Sinkronisasi batas administrasi & poligon wilayah spasial...',
  'Validasi citra satelit & integrasi data bencana BMKG...',
  'Kalkulasi estimasi populasi terdampak (WorldPop 100m)...',
  'Optimasi alokasi rantai pasok & komoditas logistik pangan...'
];

export default function EmergencyLoadingScreen({ isVisible = true }) {
  const [stepIdx, setStepIdx] = useState(0);
  const [progress, setProgress] = useState(25);

  useEffect(() => {
    if (!isVisible) {
      setProgress(100);
      return;
    }

    setProgress(25);
    const stepInterval = setInterval(() => {
      setStepIdx(prev => (prev + 1) % LOADING_STEPS.length);
    }, 400);

    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 92) return prev;
        return prev + Math.floor(Math.random() * 12) + 6;
      });
    }, 150);

    return () => {
      clearInterval(stepInterval);
      clearInterval(progressInterval);
    };
  }, [isVisible]);

  return (
    <div className={`emergency-loading-overlay ${!isVisible ? 'fade-out' : ''}`}>
      <div className="emergency-loading-card">
        {/* Clean JS Spinner Icon from react-icons */}
        <div className="clean-spinner-wrapper">
          <TbLoader2 className="clean-spinner-icon" />
        </div>

        {/* Institutional System Badge */}
        <div className="loading-badge">
          <TbDatabase style={{ fontSize: '13px' }} />
          <span>SISTEM PENDUKUNG KEPUTUSAN SPASIAL · SDSS</span>
        </div>

        <h2 className="loading-title">Logistik Pangan Pasca-Bencana</h2>
        
        {/* Rotating Step Text with JS Map Icon */}
        <p className="loading-step-text">
          <TbMap2 className="step-icon-js" />
          <span>{LOADING_STEPS[stepIdx]}</span>
        </p>

        {/* Clean Progress Track */}
        <div className="loading-progress-track">
          <div 
            className="loading-progress-bar" 
            style={{ width: `${Math.min(100, progress)}%` }}
          />
        </div>

        {/* Institutional System Chips with JS Icons */}
        <div className="loading-system-chips">
          <span className="system-chip">
            <TbSatellite style={{ marginRight: 5, fontSize: '13px' }} /> Citra Satelit VHR
          </span>
          <span className="system-chip">
            <TbUsers style={{ marginRight: 5, fontSize: '13px' }} /> WorldPop 100m
          </span>
          <span className="system-chip">
            <TbShieldCheck style={{ marginRight: 5, fontSize: '13px' }} /> Data BMKG & BNPB
          </span>
        </div>
      </div>
    </div>
  );
}
