import React from 'react';
import { LuList, LuMapPin, LuTriangleAlert, LuPackage, LuDroplet, LuBox, LuArchive } from 'react-icons/lu';
import '../styles/LogisticsTable.css';

export default function LogisticsTable({ data, onRowClick }) {
  const redZones = data?.map_data?.red_zones || [];

  if (!redZones.length) {
    return (
      <div className="logistics-card">
        <div className="logistics-header">
          <span className="logistics-header-icon"><LuList /></span>
          <h3>Daftar Area Terdampak</h3>
        </div>
        <p className="table-empty">Menunggu data backend...</p>
      </div>
    );
  }

  return (
    <div className="logistics-card">
      <div className="logistics-header">
        <span className="logistics-header-icon"><LuList /></span>
        <h3>Daftar Area Terdampak</h3>
      </div>
      <div className="table-container">
        {redZones.map((zone, i) => (
          <div className="table-row" key={i} onClick={() => onRowClick(zone)}>
            <div className="row-header">
              <span className="row-title">{zone.desa}</span>
              <span className="row-badge">{zone.count} Kerusakan</span>
            </div>
            <div className="row-details">
              <span className="row-detail-item">
                <LuTriangleAlert size={14} /> {zone.disaster_type || 'Bencana Alam'}
              </span>
              <span className="row-detail-item">
                <LuMapPin size={14} /> {zone.lon.toFixed(4)}, {zone.lat.toFixed(4)}
              </span>
            </div>
            {zone.logistics && (
              <div className="row-logistics">
                <span className="logistics-item">
                  <LuPackage size={13} /> Beras: {zone.logistics.beras} kg
                </span>
                <span className="logistics-item">
                  <LuDroplet size={13} /> Air: {zone.logistics.air} L
                </span>
                <span className="logistics-item">
                  <LuBox size={13} /> Mie: {zone.logistics.mie} dus
                </span>
                <span className="logistics-item">
                  <LuArchive size={13} /> Lauk: {zone.logistics.lauk} pkt
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
