import React from "react";
import DeckGL from "@deck.gl/react";
import { Map } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import "../styles/DeckMap.css";

export default function DeckMap({
  viewState,
  setViewState,
  layers,
  onMarkerClick,
}) {
  const handleClick = (info) => {
    console.log("🖱️ DeckGL onClick fired!");
    console.log("Info:", info);
    console.log("Object:", info?.object);
    console.log("Layer:", info?.layer?.id);

    // IMPORTANT: Check if object exists - if click is on a layer object
    if (info?.object && Object.keys(info.object).length > 0) {
      console.log("✅ Layer object detected:", info.object);
      // Force callback with confirmed object
      if (onMarkerClick) {
        onMarkerClick(info.object);
      }
    } else if (info?.picked) {
      // Alternative check for picked objects
      console.log("✅ Picked object confirmed:", info.object);
      if (onMarkerClick) {
        onMarkerClick(info.object);
      }
    } else {
      console.log("❌ No object detected on click");
    }
  };

  // Additional event tracking
  const handleHover = (info) => {
    // Hover state can be used for cursor change
    if (info?.object) {
      console.log("🎯 Hovering over:", info.object.desa);
    }
  };

  return (
    <DeckGL
      initialViewState={viewState}
      onViewStateChange={({ viewState }) => setViewState(viewState)}
      controller={true}
      layers={layers}
      onClick={handleClick}
      onHover={handleHover}
      pickingRadius={5}
      useDevicePixels={true}
      style={{ background: "#000000" }}
      getTooltip={({ object, x, y }) => {
        if (!object) return null;
        if (object.count !== undefined) {
          const type = object.disaster_type || "Bencana Alam";
          const desa = object.desa || "Tidak Diketahui";
          let text = `${type.toUpperCase()}\n\nDesa: ${desa}\nKerusakan: ${object.count} unit\nEst. Terdampak: ${object.count * 4} jiwa`;
          if (object.logistics) {
            text += `\n\nKebutuhan Logistik`;
            text += `\nBeras: ${object.logistics.beras} kg`;
            text += `\nAir: ${object.logistics.air} L`;
            text += `\nMie: ${object.logistics.mie} dus`;
            text += `\nLauk: ${object.logistics.lauk} pkt`;
          }
          return { text, x, y };
        }
        return null;
      }}
    >
      <Map
        mapStyle={{
          version: 8,
          sources: {
            satellite: {
              type: "raster",
              tiles: [
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
              ],
              tileSize: 256,
            },
          },
          layers: [
            {
              id: "satellite-layer",
              type: "raster",
              source: "satellite",
              minzoom: 0,
              maxzoom: 19,
            },
          ],
        }}
      />
    </DeckGL>
  );
}
