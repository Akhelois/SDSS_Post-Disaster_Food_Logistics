import React, { useState, useRef, useEffect } from "react";
import { LuGripVertical } from "react-icons/lu";
import RealtimeNews from "./RealtimeNews";
import LiveStreams from "./LiveStreams";
import "../styles/BottomSheet.css";

export default function BottomSheet() {
  const [sheetHeight, setSheetHeight] = useState(140); // Initial height in pixels
  const [isDragging, setIsDragging] = useState(false);
  const sheetRef = useRef(null);
  const dragStartY = useRef(0);
  const startHeight = useRef(0);

  const maxHeight = window.innerHeight * 0.7; // Max 70% of page height (increased from 40%)
  const minHeight = 100;

  const handleDragStart = (e) => {
    setIsDragging(true);
    dragStartY.current = e.clientY || e.touches?.[0]?.clientY || 0;
    startHeight.current = sheetHeight;
  };

  const handleDragMove = (e) => {
    if (!isDragging) return;

    const currentY = e.clientY || e.touches?.[0]?.clientY || 0;
    const diff = dragStartY.current - currentY; // Negative = dragging down
    const newHeight = Math.max(
      minHeight,
      Math.min(maxHeight, startHeight.current + diff),
    );
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

  useEffect(() => {
    const handleResize = () => {
      const newMaxHeight = window.innerHeight * 0.7;
      if (sheetHeight > newMaxHeight) {
        setSheetHeight(newMaxHeight);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [sheetHeight]);

  return (
    <div
      ref={sheetRef}
      className="bottom-sheet"
      style={{ height: `${sheetHeight}px` }}
    >
      <div
        className="drag-handle"
        onMouseDown={handleDragStart}
        onTouchStart={handleDragStart}
      >
        <LuGripVertical size={20} />
      </div>

      <div className="sheet-content">
        <div className="content-column news-column">
          <RealtimeNews />
        </div>
        <div className="content-column streams-column">
          <LiveStreams />
        </div>
      </div>
    </div>
  );
}
