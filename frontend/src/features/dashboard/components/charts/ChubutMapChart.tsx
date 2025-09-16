"use client";

import React, { useState, useEffect, useRef } from "react";
import { ChubutSvg } from "@/components/chubut.svg";
import {
  DEPARTAMENTO_INDEC_TO_SVG,
  getSvgIdFromIndec,
} from "../../constants/chubut-mapping";

interface DepartmentData {
  codigo_indec: number;
  nombre: string;
  zona_ugd: string;
  poblacion: number;
  casos: number;
  tasa_incidencia: number;
}

interface ChubutMapChartProps {
  data: {
    departamentos: DepartmentData[];
    total_casos: number;
  };
}

const ChubutMapChart: React.FC<ChubutMapChartProps> = ({ data }) => {
  const [hoveredDept, setHoveredDept] = useState<DepartmentData | null>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const svgRef = useRef<HTMLDivElement>(null);

  console.log("ChubutMapChart", data);

  // Crear mapa de datos por SVG ID
  const dataByDeptId = React.useMemo(() => {
    const map = new Map<string, DepartmentData>();
    data.departamentos.forEach((dept) => {
      const svgId = getSvgIdFromIndec(dept.codigo_indec);
      if (svgId) {
        map.set(svgId, dept);
      }
    });
    return map;
  }, [data.departamentos]);

  // Calcular el color basado en la tasa de incidencia
  const getColorForDepartment = (svgId: string): string => {
    const dept = dataByDeptId.get(svgId);
    if (!dept) return "#e0e0e0";

    const tasa = dept.tasa_incidencia;
    if (tasa === 0) return "#f0f0f0";
    if (tasa < 10) return "#fee0d2";
    if (tasa < 50) return "#fcbba1";
    if (tasa < 100) return "#fc9272";
    if (tasa < 200) return "#fb6a4a";
    if (tasa < 500) return "#ef3b2c";
    return "#cb181d";
  };

  // Add colors and hover handlers to SVG paths
  useEffect(() => {
    if (!svgRef.current) return;

    const svgElement = svgRef.current.querySelector("svg");
    if (!svgElement) return;

    // Find all department groups
    const departmentGroups = svgElement.querySelectorAll("g[id]");

    departmentGroups.forEach((group) => {
      const deptId = group.id;
      const deptData = dataByDeptId.get(deptId);

      if (deptData) {
        // Find the path element within the group
        const pathElement = group.querySelector("path");
        if (pathElement) {
          // Set the fill color
          pathElement.style.fill = getColorForDepartment(deptId);
          pathElement.style.cursor = "pointer";
          pathElement.style.transition = "all 0.2s ease";

          // Add hover handlers
          const handleMouseEnter = (e: MouseEvent) => {
            pathElement.style.opacity = "0.8";
            pathElement.style.stroke = "#333";
            pathElement.style.strokeWidth = "2";
            setHoveredDept(deptData);
            setMousePosition({ x: e.clientX, y: e.clientY });
          };

          const handleMouseMove = (e: MouseEvent) => {
            setMousePosition({ x: e.clientX, y: e.clientY });
          };

          const handleMouseLeave = () => {
            pathElement.style.opacity = "1";
            pathElement.style.stroke = "#666";
            pathElement.style.strokeWidth = "0.5";
            setHoveredDept(null);
          };

          pathElement.addEventListener("mouseenter", handleMouseEnter);
          pathElement.addEventListener("mousemove", handleMouseMove);
          pathElement.addEventListener("mouseleave", handleMouseLeave);

          // Cleanup
          return () => {
            pathElement.removeEventListener("mouseenter", handleMouseEnter);
            pathElement.removeEventListener("mousemove", handleMouseMove);
            pathElement.removeEventListener("mouseleave", handleMouseLeave);
          };
        }
      }
    });
  }, [dataByDeptId]);

  return (
    <div className="relative w-full h-full">
      <div ref={svgRef} className="w-full h-full">
        <ChubutSvg className="w-full h-auto" />
      </div>

      {/* Tooltip */}
      {hoveredDept && (
        <div
          className="absolute z-50 bg-white rounded-lg shadow-lg p-3 pointer-events-none"
          style={{
            left: mousePosition.x + 10,
            top: mousePosition.y - 10,
            transform: "translate(0, -100%)",
          }}
        >
          <div className="font-semibold text-sm">{hoveredDept.nombre}</div>
          <div className="text-xs text-gray-600 mt-1">
            <div>Zona: {hoveredDept.zona_ugd}</div>
            <div>Población: {hoveredDept.poblacion.toLocaleString()}</div>
            <div>Casos: {hoveredDept.casos}</div>
            <div>
              Tasa: {hoveredDept.tasa_incidencia.toFixed(2)} por 100.000 hab.
            </div>
          </div>
        </div>
      )}

      {/* Leyenda */}
      <div className="absolute bottom-4 left-4 bg-white rounded p-2 shadow">
        <div className="text-xs font-semibold mb-1">Tasa de incidencia</div>
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-1">
            <div
              className="w-4 h-3"
              style={{ backgroundColor: "#f0f0f0" }}
            ></div>
            <span className="text-xs">Sin casos</span>
          </div>
          <div className="flex items-center gap-1">
            <div
              className="w-4 h-3"
              style={{ backgroundColor: "#fee0d2" }}
            ></div>
            <span className="text-xs">&lt; 10</span>
          </div>
          <div className="flex items-center gap-1">
            <div
              className="w-4 h-3"
              style={{ backgroundColor: "#fcbba1" }}
            ></div>
            <span className="text-xs">10 - 50</span>
          </div>
          <div className="flex items-center gap-1">
            <div
              className="w-4 h-3"
              style={{ backgroundColor: "#fc9272" }}
            ></div>
            <span className="text-xs">50 - 100</span>
          </div>
          <div className="flex items-center gap-1">
            <div
              className="w-4 h-3"
              style={{ backgroundColor: "#fb6a4a" }}
            ></div>
            <span className="text-xs">100 - 200</span>
          </div>
          <div className="flex items-center gap-1">
            <div
              className="w-4 h-3"
              style={{ backgroundColor: "#ef3b2c" }}
            ></div>
            <span className="text-xs">200 - 500</span>
          </div>
          <div className="flex items-center gap-1">
            <div
              className="w-4 h-3"
              style={{ backgroundColor: "#cb181d" }}
            ></div>
            <span className="text-xs">&gt; 500</span>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="absolute top-4 right-4 bg-white rounded p-2 shadow">
        <div className="text-xs font-semibold">Total Provincial</div>
        <div className="text-lg font-bold">{data.total_casos} casos</div>
      </div>
    </div>
  );
};

export default ChubutMapChart;
