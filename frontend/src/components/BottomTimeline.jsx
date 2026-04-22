import React, { useState, useRef, useEffect } from "react";
import { LuPlay, LuPause, LuRotateCcw, LuGripVertical } from "react-icons/lu";
import "../styles/BottomTimeline.css";

export default function BottomTimeline({ onTimeChange }) {
  const [timeValue, setTimeValue] = useState(50);
  const [isPlaying, setIsPlaying] = useState(false);
  const [sheetHeight, setSheetHeight] = useState(120); // Height in pixels
  const [isDragging, setIsDragging] = useState(false);
  const sheetRef = useRef(null);
  const dragStartY = useRef(0);
  const startHeight = useRef(0);

  const handleTimeChange = (e) => {
    const value = parseInt(e.target.value);
    setTimeValue(value);
    onTimeChange?.(value);
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    setTimeValue(0);
    setIsPlaying(false);
  };

  // Drag handlers
  const handleDragStart = (e) => {
    setIsDragging(true);
    dragStartY.current = e.clientY || e.touches?.[0]?.clientY || 0;
    startHeight.current = sheetHeight;
  };

  const handleDragMove = (e) => {
    if (!isDragging) return;

    const currentY = e.clientY || e.touches?.[0]?.clientY || 0;
    const diff = dragStartY.current - currentY; // Negative = dragging down
    const newHeight = Math.max(120, Math.min(400, startHeight.current + diff));
    setSheetHeight(newHeight);
  };

  const handleDragEnd = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener("mousemove", handleDragMove);
      document.addEventListener("mouseup", handleDragEnd);
      document.addEventListener("touchmove", handleDragMove);
      document.addEventListener("touchend", handleDragEnd);

      return () => {
        document.removeEventListener("mousemove", handleDragMove);
        document.removeEventListener("mouseup", handleDragEnd);
        document.removeEventListener("touchmove", handleDragMove);
        document.removeEventListener("touchend", handleDragEnd);
      };
    }
  }, [isDragging]);

  // Mock timeline data
  const startDate = new Date("2024-01-01");
  const endDate = new Date("2024-12-31");
  const currentDate = new Date(
    startDate.getTime() +
      (timeValue / 100) * (endDate.getTime() - startDate.getTime()),
  );

  return (
    <div
      ref={sheetRef}
      className="bottom-timeline"
      style={{ height: `${sheetHeight}px` }}
    >
      <div
        className="drag-handle"
        onMouseDown={handleDragStart}
        onTouchStart={handleDragStart}
      >
        <LuGripVertical size={20} />
      </div>

      <div className="timeline-content">
        <div className="timeline-controls">
          <button
            className={`control-btn ${isPlaying ? "playing" : ""}`}
            onClick={handlePlayPause}
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <LuPause size={18} /> : <LuPlay size={18} />}
          </button>
          <button className="control-btn" onClick={handleReset} title="Reset">
            <LuRotateCcw size={18} />
          </button>
        </div>

        <div className="timeline-display">
          <span className="date-label">
            {currentDate.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
            })}
          </span>
          <div className="progress-info">
            <span className="progress-text">Animating data over time</span>
          </div>
        </div>

        <div className="timeline-slider-container">
          <input
            type="range"
            min="0"
            max="100"
            value={timeValue}
            onChange={handleTimeChange}
            className="timeline-slider"
          />
          <div className="timeline-labels">
            <span>Jan 2024</span>
            <span>Jul 2024</span>
            <span>Dec 2024</span>
          </div>
        </div>

        <div className="timeline-stats">
          <div className="stat-badge">
            <span className="badge-label">Progress</span>
            <span className="badge-value">{timeValue}%</span>
          </div>
          <div className="stat-badge">
            <span className="badge-label">Events</span>
            <span className="badge-value">342</span>
          </div>
          <div className="stat-badge">
            <span className="badge-label">Updates</span>
            <span className="badge-value">128</span>
          </div>
        </div>
      </div>
    </div>
  );
}
