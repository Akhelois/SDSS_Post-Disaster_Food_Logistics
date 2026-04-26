import React from 'react';
import { LuRadar, LuTriangleAlert } from 'react-icons/lu';
import '../styles/SidebarHeader.css';

export default function SidebarHeader({ disasterInfo }) {
  return (
    <div className="header">
      <div className="header-top">
        <LuRadar className="header-logo" />
        <div>
          <h1>SDSS Logistik Bencana</h1>
          <p>Damage Assessment & Logistics Estimation</p>
        </div>
      </div>
      {disasterInfo && disasterInfo.summary && (
        <div className="disaster-tag">
          <LuTriangleAlert size={13} />
          <span>{disasterInfo.summary}</span>
        </div>
      )}
    </div>
  );
}
