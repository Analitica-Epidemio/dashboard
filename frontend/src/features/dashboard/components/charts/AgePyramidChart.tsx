"use client";

import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

interface PyramidDataPoint {
  age: string;
  sex: "M" | "F";
  value: number;
}

interface AgePyramidChartProps {
  data: PyramidDataPoint[];
  width?: number;
  height?: number;
  className?: string;
}

export function AgePyramidChart({
  data,
  width = 800,
  height = 500,
  className = "",
}: AgePyramidChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  console.log({ data });

  useEffect(() => {
    if (!data || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Limpiar contenido previo

    const margin = { top: 20, right: 60, bottom: 30, left: 60 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    // Obtener grupos de edad únicos y ordenarlos
    const ageGroups = [...new Set(data.map((d) => d.age))];
    const sortedAgeGroups = [
      "0-4",
      "5-9",
      "10-14",
      "15-19",
      "20-24",
      "25-29",
      "30-34",
      "35-39",
      "40-44",
      "45-49",
      "50-54",
      "55-59",
      "60-64",
      "65+",
    ].filter((age) => ageGroups.includes(age));

    // Separar datos por sexo
    const maleData = data.filter((d) => d.sex === "M");
    const femaleData = data.filter((d) => d.sex === "F");

    // Encontrar el valor máximo para las escalas
    const maxValue = Math.max(...data.map((d) => d.value));

    // Configurar escalas
    const yScale = d3
      .scaleBand()
      .domain(sortedAgeGroups)
      .range([chartHeight, 0])
      .padding(0.1);

    const xScaleLeft = d3
      .scaleLinear()
      .domain([0, maxValue])
      .range([chartWidth / 2, 0]);

    const xScaleRight = d3
      .scaleLinear()
      .domain([0, maxValue])
      .range([chartWidth / 2, chartWidth]);

    // Crear contenedor principal
    const g = svg
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Dibujar barras masculinas (izquierda)
    g.selectAll(".bar-male")
      .data(maleData)
      .enter()
      .append("rect")
      .attr("class", "bar-male")
      .attr("fill", "#3b82f6") // Azul
      .attr("x", (d) => xScaleLeft(d.value))
      .attr("y", (d) => yScale(d.age)!)
      .attr("width", (d) => xScaleLeft(0) - xScaleLeft(d.value))
      .attr("height", yScale.bandwidth())
      .attr("opacity", 0.7);

    // Dibujar barras femeninas (derecha)
    g.selectAll(".bar-female")
      .data(femaleData)
      .enter()
      .append("rect")
      .attr("class", "bar-female")
      .attr("fill", "#ef4444") // Rojo
      .attr("x", chartWidth / 2)
      .attr("y", (d) => yScale(d.age)!)
      .attr("width", (d) => xScaleRight(d.value) - xScaleRight(0))
      .attr("height", yScale.bandwidth())
      .attr("opacity", 0.7);

    // Agregar etiquetas de valores en las barras masculinas
    g.selectAll(".label-male")
      .data(maleData.filter((d) => d.value > 0))
      .enter()
      .append("text")
      .attr("class", "label-male")
      .attr("text-anchor", "end")
      .attr("x", (d) => xScaleLeft(d.value) - 4)
      .attr("y", (d) => yScale(d.age)! + yScale.bandwidth() / 2)
      .attr("dy", "0.35em")
      .attr("fill", "white")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .text((d) => d.value.toLocaleString());

    // Agregar etiquetas de valores en las barras femeninas
    g.selectAll(".label-female")
      .data(femaleData.filter((d) => d.value > 0))
      .enter()
      .append("text")
      .attr("class", "label-female")
      .attr("text-anchor", "start")
      .attr("x", (d) => xScaleRight(d.value) + 4)
      .attr("y", (d) => yScale(d.age)! + yScale.bandwidth() / 2)
      .attr("dy", "0.35em")
      .attr("fill", "white")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .text((d) => d.value.toLocaleString());

    // Agregar eje Y (grupos de edad)
    const yAxis = d3.axisLeft(yScale);
    g.append("g")
      .attr("class", "y-axis")
      .attr("transform", `translate(${chartWidth / 2}, 0)`)
      .call(yAxis)
      .selectAll("text")
      .attr("font-size", "12px")
      .attr("fill", "#374151");

    // Agregar eje X izquierdo (masculino)
    const xAxisLeft = d3
      .axisBottom(xScaleLeft)
      .tickFormat((d) => Math.abs(d as number).toLocaleString());

    g.append("g")
      .attr("class", "x-axis-left")
      .attr("transform", `translate(0, ${chartHeight})`)
      .call(xAxisLeft)
      .selectAll("text")
      .attr("font-size", "10px")
      .attr("fill", "#6b7280");

    // Agregar eje X derecho (femenino)
    const xAxisRight = d3.axisBottom(xScaleRight);
    g.append("g")
      .attr("class", "x-axis-right")
      .attr("transform", `translate(0, ${chartHeight})`)
      .call(xAxisRight)
      .selectAll("text")
      .attr("font-size", "10px")
      .attr("fill", "#6b7280");

    // Agregar línea central
    g.append("line")
      .attr("x1", chartWidth / 2)
      .attr("x2", chartWidth / 2)
      .attr("y1", 0)
      .attr("y2", chartHeight)
      .attr("stroke", "#d1d5db")
      .attr("stroke-width", 1);

    // Agregar etiquetas de sexo
    g.append("text")
      .attr("text-anchor", "end")
      .attr("x", chartWidth / 2 - 10)
      .attr("y", -5)
      .attr("fill", "#3b82f6")
      .attr("font-size", "14px")
      .attr("font-weight", "bold")
      .text("Masculino");

    g.append("text")
      .attr("text-anchor", "start")
      .attr("x", chartWidth / 2 + 10)
      .attr("y", -5)
      .attr("fill", "#ef4444")
      .attr("font-size", "14px")
      .attr("font-weight", "bold")
      .text("Femenino");

    // Agregar título del eje Y
    g.append("text")
      .attr("text-anchor", "middle")
      .attr("transform", `rotate(-90)`)
      .attr("x", -chartHeight / 2)
      .attr("y", -40)
      .attr("fill", "#374151")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .text("Grupos de Edad");

    // Agregar título del eje X
    g.append("text")
      .attr("text-anchor", "middle")
      .attr("x", chartWidth / 2)
      .attr("y", chartHeight + margin.bottom)
      .attr("fill", "#374151")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .text("Número de Casos");
  }, [data, width, height]);

  // Si no hay datos, mostrar mensaje
  if (!data || data.length === 0) {
    return (
      <div className={`population-pyramid ${className}`}>
        <div className="flex items-center justify-center h-64 text-gray-500">
          No hay datos disponibles para la pirámide poblacional
        </div>
      </div>
    );
  }

  return (
    <div className={`population-pyramid ${className}`}>
      <svg ref={svgRef} className="w-full h-auto" />
    </div>
  );
}

export default AgePyramidChart;
