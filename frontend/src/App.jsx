import React, { useState, useEffect } from 'react';
import { PolygonLayer, PathLayer } from '@deck.gl/layers';
import axios from 'axios';
import './styles/App.css';

import DeckMap from './components/DeckMap';
import SidebarHeader from './components/SidebarHeader';
import MetricCards from './components/MetricCards';
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

  useEffect(() => {
    // Fetch data from FastAPI
    axios.get('http://127.0.0.1:8000/')
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
    // Rute Darat Background (Outline)
    ...(mapData.paths?.outline?.length > 0 ? [
      new PathLayer({
        id: 'path-outline',
        data: mapData.paths.outline,
        getPath: d => d.path,
        getColor: [255, 255, 255, 70],
        getWidth: 12,
        widthMinPixels: 8,
        rounded: true,
        pickable: false
      })
    ] : []),
    // Rute Darat
    ...(mapData.paths?.blue?.length > 0 ? [
      new PathLayer({
        id: 'path-blue',
        data: mapData.paths.blue,
        getPath: d => d.path,
        getColor: [56, 189, 248, 230],
        getWidth: 7,
        widthMinPixels: 5,
        rounded: true,
        pickable: true
      })
    ] : []),
    // Rute Darat Link
    ...(mapData.paths?.link?.length > 0 ? [
      new PathLayer({
        id: 'path-blue-link',
        data: mapData.paths.link,
        getPath: d => d.path,
        getColor: [56, 189, 248, 210],
        getWidth: 4,
        widthMinPixels: 3,
        rounded: true,
        pickable: false
      })
    ] : []),
    // Jalur Laut / Udara
    ...(mapData.paths?.air?.length > 0 ? [
      new PathLayer({
        id: 'path-air',
        data: mapData.paths.air,
        getPath: d => d.path,
        getColor: [249, 115, 22, 190],
        getWidth: 3,
        widthMinPixels: 2,
        rounded: true,
        pickable: false
      })
    ] : []),
    // Zona Kerusakan (Polygon mengikuti bentuk damage)
    ...(mapData.red_zones?.length > 0 ? [
      new PolygonLayer({
        id: 'damage-zones',
        data: mapData.red_zones.filter(d => d.polygon),
        getPolygon: d => d.polygon,
        getFillColor: [239, 68, 68, 60],
        getLineColor: [248, 113, 113, 200],
        lineWidthMinPixels: 2,
        filled: true,
        stroked: true,
        pickable: true,
        extruded: false
      })
    ] : [])
  ];

  const handleRowClick = (hub) => {
    setViewState({
      ...viewState,
      longitude: hub.lon, 
      latitude: hub.lat,
      zoom: 13.5,
      transitionDuration: 1000
    });
  };

  return (
    <div className="dashboard-layout">
      {loading && <LoadingOverlay />}

      <div className="map-container">
        <DeckMap viewState={viewState} setViewState={setViewState} layers={layers} />
      </div>

      <div className="sidebar">
        <SidebarHeader disasterInfo={data?.disaster_info} />
        <MetricCards metrics={data?.metrics} />
        <LogisticsTable data={data} onRowClick={handleRowClick} />
      </div>
    </div>
  );
}
