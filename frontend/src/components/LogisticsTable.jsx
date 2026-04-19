import React from 'react';
import { LuList, LuMapPin, LuNavigation, LuPackage, LuDroplet, LuBox, LuArchive } from 'react-icons/lu';
import '../styles/LogisticsTable.css';

export default function LogisticsTable({ data, onRowClick }) {
  if (!data) {
    return (
      <div className="logistics-card">
        <div className="logistics-header">
          <span className="logistics-header-icon"><LuList /></span>
          <h3>Daftar Distribusi Logistik</h3>
        </div>
        <p className="table-empty">Menunggu data backend...</p>
      </div>
    );
  }

  return (
    <div className="logistics-card">
      <div className="logistics-header">
        <span className="logistics-header-icon"><LuList /></span>
        <h3>Daftar Distribusi Logistik</h3>
      </div>
      <div className="table-container">
        {data.hubs.map((hub, i) => (
          <div className="table-row" key={i} onClick={() => onRowClick(hub)}>
            <div className="row-header">
              <span className="row-title">Hub {hub.id}</span>
              <span className="row-badge">{hub.damage} Rusak</span>
            </div>
            <div className="row-details">
              <span className="row-detail-item">
                <LuMapPin size={14} /> {hub.desa}
              </span>
              <span className="row-detail-item">
                <LuNavigation size={14} /> Jangkauan: {hub.distance} km
              </span>
            </div>
            {hub.logistics && (
              <div className="row-logistics">
                <span className="logistics-item">
                  <LuPackage size={13} /> Beras: {hub.logistics.beras} kg
                </span>
                <span className="logistics-item">
                  <LuDroplet size={13} /> Air: {hub.logistics.air} L
                </span>
                <span className="logistics-item">
                  <LuBox size={13} /> Mie: {hub.logistics.mie} dus
                </span>
                <span className="logistics-item">
                  <LuArchive size={13} /> Lauk: {hub.logistics.lauk} pkt
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
