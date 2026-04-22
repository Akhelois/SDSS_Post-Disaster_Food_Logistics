import React, { useState, useEffect } from "react";
import { PolygonLayer, ScatterplotLayer } from "@deck.gl/layers";
import { FlyToInterpolator } from "@deck.gl/core";
import axios from "axios";
import "./styles/App.css";

import TopNavBar from "./components/TopNavBar";
import LeftSidebar from "./components/LeftSidebar";
import DeckMap from "./components/DeckMap";
import RightPanel from "./components/RightPanel";
import BottomSheet from "./components/BottomSheet";
import LoadingOverlay from "./components/LoadingOverlay";

const INITIAL_VIEW_STATE = {
  longitude: 115.0,
  latitude: -2.0,
  zoom: 4,
  pitch: 35,
  bearing: 0,
};

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedMarker, setSelectedMarker] = useState(null);
  const [visibleLayers, setVisibleLayers] = useState({
    disaster_zones: true,
    damage_points: true,
    relief_hubs: false,
    evacuation_routes: false,
    critical_alerts: true,
    warnings: false,
    updates: true,
    heatmap: false,
    population: false,
    logistics: false,
  });

  useEffect(() => {
    axios
      .get("http://127.0.0.1:8000/")
      .then((res) => {
        setData(res.data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const handleLayerToggle = (layerId) => {
    setVisibleLayers((prev) => ({
      ...prev,
      [layerId]: !prev[layerId],
    }));
  };

  const handleMarkerClick = (marker) => {
    console.log("🎯🎯🎯 MARKER CLICKED IN APP 🎯🎯🎯");
    console.log("Marker data:", marker);
    console.log("Setting selectedMarker state...");

    // Ensure marker has required fields
    if (marker && marker.desa) {
      setSelectedMarker(marker);
      console.log("✅ State set successfully!");
    } else {
      console.log("❌ Invalid marker data:", marker);
    }
  };

  // Debug: log whenever selectedMarker changes
  useEffect(() => {
    console.log("🔔 selectedMarker state changed to:", selectedMarker);
  }, [selectedMarker]);

  const mapData = data?.map_data || {};

  const layers = [
    // Disaster Zones Layer
    ...(visibleLayers.disaster_zones && mapData.red_zones?.length > 0
      ? [
          new PolygonLayer({
            id: "damage-zones",
            data: mapData.red_zones.filter((d) => d.polygon),
            getPolygon: (d) => d.polygon,
            getFillColor: [239, 68, 68, 60],
            getLineColor: [248, 113, 113, 200],
            lineWidthMinPixels: 2,
            filled: true,
            stroked: true,
            pickable: true,
            extruded: false,
          }),
        ]
      : []),

    // Damage Points Layer
    ...(visibleLayers.damage_points && mapData.red_zones?.length > 0
      ? [
          new ScatterplotLayer({
            id: "damage-points",
            data: mapData.red_zones,
            getPosition: (d) => [d.lon, d.lat],
            getRadius: (d) => Math.max(d.count * 10, 500),
            getFillColor: [249, 115, 22, 180],
            getLineColor: [255, 255, 255, 200],
            lineWidthMinPixels: 1,
            pickable: true,
            radiusScale: 1,
          }),
        ]
      : []),

    // Relief Hubs Layer
    ...(visibleLayers.relief_hubs && mapData.red_zones?.length > 0
      ? [
          new ScatterplotLayer({
            id: "relief-hubs",
            data: mapData.red_zones.slice(0, 5),
            getPosition: (d) => [d.lon, d.lat],
            getRadius: 800,
            getFillColor: [16, 185, 129, 200],
            lineWidthMinPixels: 2,
            pickable: true,
          }),
        ]
      : []),
  ];

  return (
    <div className="dashboard-layout">
      {loading && <LoadingOverlay />}

      <TopNavBar onMenuClick={() => setSidebarOpen(!sidebarOpen)} />

      <div className="dashboard-main">
        <LeftSidebar
          visibleLayers={visibleLayers}
          onLayerToggle={handleLayerToggle}
        />

        <div className="map-section">
          <DeckMap
            viewState={viewState}
            setViewState={setViewState}
            layers={layers}
            onMarkerClick={handleMarkerClick}
          />
        </div>

        <RightPanel
          selectedMarker={selectedMarker}
          allLocations={mapData.red_zones || []}
          onClose={() => setSelectedMarker(null)}
          onSelectLocation={(marker) => setSelectedMarker(marker)}
        />
      </div>

      <BottomSheet />
    </div>
  );
}
