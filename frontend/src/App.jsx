import React, { useState, useEffect } from 'react';
import { PolygonLayer } from '@deck.gl/layers';
import { FlyToInterpolator } from '@deck.gl/core';
import axios from 'axios';
import './styles/App.css';

import DeckMap from './components/DeckMap';
import SidebarHeader from './components/SidebarHeader';
import MetricCards from './components/MetricCards';
import NewsPanel from './components/NewsPanel';
import LogisticsTable from './components/LogisticsTable';
import LoadingOverlay from './components/LoadingOverlay';

const INITIAL_VIEW_STATE = {
  longitude: 115.0,
  latitude: -2.0,
  zoom: 4,
  pitch: 35,
  bearing: 0
};

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
  const API_BASE = import.meta.env.VITE_API_URL || '/api/';

  useEffect(() => {
    axios.get(API_BASE)
      .then(res => {
        setData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const mapData = data?.map_data || {};

  const layers = [
    ...(mapData.red_zones?.length > 0 ? [
      new PolygonLayer({
        id: 'damage-zones',
        data: mapData.red_zones.filter(d => d.polygon),
        getPolygon: d => d.polygon,
        getFillColor: [224, 82, 82, 50],
        getLineColor: [224, 82, 82, 180],
        lineWidthMinPixels: 1.5,
        filled: true,
        stroked: true,
        pickable: true,
        extruded: false
      })
    ] : [])
  ];

  const handleRowClick = (item) => {
    setViewState({
      ...viewState,
      longitude: item.lon,
      latitude: item.lat,
      zoom: 13.5,
      transitionDuration: 1500,
      transitionInterpolator: new FlyToInterpolator()
    });
  };

  return (
    <div className="dashboard-layout">
      {loading && <LoadingOverlay />}

      <div className="sidebar">
        <SidebarHeader disasterInfo={data?.disaster_info} />
        <MetricCards metrics={data?.metrics} />
        {/* <NewsPanel /> */}
        <LogisticsTable data={data} onRowClick={handleRowClick} />
      </div>

      <div className="map-container">
        <DeckMap viewState={viewState} setViewState={setViewState} layers={layers} />
      </div>
    </div>
  );
}
