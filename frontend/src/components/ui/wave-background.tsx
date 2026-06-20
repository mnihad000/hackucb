"use client";

import * as React from "react";
import { useEffect, useRef } from "react";
import { createNoise2D } from "simplex-noise";

interface Point {
  x: number;
  y: number;
  wave: { x: number; y: number };
  cursor: {
    x: number;
    y: number;
    vx: number;
    vy: number;
  };
}

interface WavesProps {
  className?: string;
  strokeColor?: string;
  backgroundColor?: string;
  pointerSize?: number;
}

export function Waves({
  className = "",
  strokeColor = "#ffffff",
  backgroundColor = "#000000",
  pointerSize = 0.5,
}: WavesProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const mouseRef = useRef({
    x: -10,
    y: 0,
    lx: 0,
    ly: 0,
    sx: 0,
    sy: 0,
    v: 0,
    vs: 0,
    a: 0,
    set: false,
  });
  const pathsRef = useRef<SVGPathElement[]>([]);
  const linesRef = useRef<Point[][]>([]);
  const noiseRef = useRef<((x: number, y: number) => number) | null>(null);
  const rafRef = useRef<number | null>(null);
  const boundingRef = useRef<DOMRect | null>(null);

  useEffect(() => {
    if (!containerRef.current || !svgRef.current) {
      return;
    }

    noiseRef.current = createNoise2D();
    setSize();
    setLines();

    window.addEventListener("resize", onResize);
    window.addEventListener("mousemove", onMouseMove);
    containerRef.current.addEventListener("touchmove", onTouchMove, {
      passive: false,
    });

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }

      window.removeEventListener("resize", onResize);
      window.removeEventListener("mousemove", onMouseMove);
      containerRef.current?.removeEventListener("touchmove", onTouchMove);
    };
  }, []);

  const setSize = () => {
    if (!containerRef.current || !svgRef.current) {
      return;
    }

    boundingRef.current = containerRef.current.getBoundingClientRect();
    const { width, height } = boundingRef.current;

    svgRef.current.style.width = `${width}px`;
    svgRef.current.style.height = `${height}px`;
  };

  const setLines = () => {
    if (!svgRef.current || !boundingRef.current) {
      return;
    }

    const { width, height } = boundingRef.current;
    linesRef.current = [];

    pathsRef.current.forEach((path) => {
      path.remove();
    });
    pathsRef.current = [];

    const xGap = 8;
    const yGap = 8;
    const oWidth = width + 200;
    const oHeight = height + 30;
    const totalLines = Math.ceil(oWidth / xGap);
    const totalPoints = Math.ceil(oHeight / yGap);
    const xStart = (width - xGap * totalLines) / 2;
    const yStart = (height - yGap * totalPoints) / 2;

    for (let i = 0; i < totalLines; i += 1) {
      const points: Point[] = [];

      for (let j = 0; j < totalPoints; j += 1) {
        points.push({
          x: xStart + xGap * i,
          y: yStart + yGap * j,
          wave: { x: 0, y: 0 },
          cursor: { x: 0, y: 0, vx: 0, vy: 0 },
        });
      }

      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.classList.add("a__line", "js-line");
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", strokeColor);
      path.setAttribute("stroke-width", "1");

      svgRef.current.appendChild(path);
      pathsRef.current.push(path);
      linesRef.current.push(points);
    }
  };

  const onResize = () => {
    setSize();
    setLines();
  };

  const onMouseMove = (event: MouseEvent) => {
    updateMousePosition(event.pageX, event.pageY);
  };

  const onTouchMove = (event: TouchEvent) => {
    event.preventDefault();
    const touch = event.touches[0];

    if (touch) {
      updateMousePosition(touch.clientX, touch.clientY);
    }
  };

  const updateMousePosition = (x: number, y: number) => {
    if (!boundingRef.current) {
      return;
    }

    const mouse = mouseRef.current;
    mouse.x = x - boundingRef.current.left;
    mouse.y = y - boundingRef.current.top + window.scrollY;

    if (!mouse.set) {
      mouse.sx = mouse.x;
      mouse.sy = mouse.y;
      mouse.lx = mouse.x;
      mouse.ly = mouse.y;
      mouse.set = true;
    }

    if (containerRef.current) {
      containerRef.current.style.setProperty("--x", `${mouse.sx}px`);
      containerRef.current.style.setProperty("--y", `${mouse.sy}px`);
    }
  };

  const movePoints = (time: number) => {
    const { current: lines } = linesRef;
    const { current: mouse } = mouseRef;
    const { current: noise } = noiseRef;

    if (!noise) {
      return;
    }

    lines.forEach((points) => {
      points.forEach((point) => {
        const move = noise(
          (point.x + time * 0.008) * 0.003,
          (point.y + time * 0.003) * 0.002,
        ) * 8;

        point.wave.x = Math.cos(move) * 12;
        point.wave.y = Math.sin(move) * 6;

        const dx = point.x - mouse.sx;
        const dy = point.y - mouse.sy;
        const distance = Math.hypot(dx, dy);
        const limit = Math.max(175, mouse.vs);

        if (distance < limit) {
          const strength = 1 - distance / limit;
          const force = Math.cos(distance * 0.001) * strength;

          point.cursor.vx += Math.cos(mouse.a) * force * limit * mouse.vs * 0.00035;
          point.cursor.vy += Math.sin(mouse.a) * force * limit * mouse.vs * 0.00035;
        }

        point.cursor.vx += (0 - point.cursor.x) * 0.01;
        point.cursor.vy += (0 - point.cursor.y) * 0.01;
        point.cursor.vx *= 0.95;
        point.cursor.vy *= 0.95;
        point.cursor.x += point.cursor.vx;
        point.cursor.y += point.cursor.vy;
        point.cursor.x = Math.min(50, Math.max(-50, point.cursor.x));
        point.cursor.y = Math.min(50, Math.max(-50, point.cursor.y));
      });
    });
  };

  const moved = (point: Point, withCursorForce = true) => ({
    x: point.x + point.wave.x + (withCursorForce ? point.cursor.x : 0),
    y: point.y + point.wave.y + (withCursorForce ? point.cursor.y : 0),
  });

  const drawLines = () => {
    const { current: lines } = linesRef;
    const { current: paths } = pathsRef;

    lines.forEach((points, lineIndex) => {
      if (points.length < 2 || !paths[lineIndex]) {
        return;
      }

      const firstPoint = moved(points[0], false);
      let d = `M ${firstPoint.x} ${firstPoint.y}`;

      for (let i = 1; i < points.length; i += 1) {
        const current = moved(points[i]);
        d += `L ${current.x} ${current.y}`;
      }

      paths[lineIndex].setAttribute("d", d);
    });
  };

  const tick = (time: number) => {
    const { current: mouse } = mouseRef;
    mouse.sx += (mouse.x - mouse.sx) * 0.1;
    mouse.sy += (mouse.y - mouse.sy) * 0.1;

    const dx = mouse.x - mouse.lx;
    const dy = mouse.y - mouse.ly;
    const distance = Math.hypot(dx, dy);

    mouse.v = distance;
    mouse.vs += (distance - mouse.vs) * 0.1;
    mouse.vs = Math.min(100, mouse.vs);
    mouse.lx = mouse.x;
    mouse.ly = mouse.y;
    mouse.a = Math.atan2(dy, dx);

    if (containerRef.current) {
      containerRef.current.style.setProperty("--x", `${mouse.sx}px`);
      containerRef.current.style.setProperty("--y", `${mouse.sy}px`);
    }

    movePoints(time);
    drawLines();
    rafRef.current = requestAnimationFrame(tick);
  };

  return (
    <div
      ref={containerRef}
      className={`waves-component relative overflow-hidden ${className}`}
      style={
        {
          "--x": "-0.5rem",
          "--y": "50%",
          backgroundColor,
          height: "100%",
          left: 0,
          margin: 0,
          overflow: "hidden",
          padding: 0,
          position: "absolute",
          top: 0,
          width: "100%",
        } as React.CSSProperties
      }
    >
      <svg
        ref={svgRef}
        className="block h-full w-full js-svg"
        xmlns="http://www.w3.org/2000/svg"
      />
      <div
        className="pointer-dot"
        style={{
          background: strokeColor,
          borderRadius: "50%",
          height: `${pointerSize}rem`,
          left: 0,
          position: "absolute",
          top: 0,
          transform: "translate3d(calc(var(--x) - 50%), calc(var(--y) - 50%), 0)",
          width: `${pointerSize}rem`,
          willChange: "transform",
        }}
      />
    </div>
  );
}
