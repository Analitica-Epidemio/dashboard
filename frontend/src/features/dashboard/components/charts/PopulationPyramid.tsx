"use client";

import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

interface PyramidDataPoint {
  age: string;
  sex: "M" | "F";
  value: number;
}

interface PopulationPyramidProps {
  data: PyramidDataPoint[];
  width?: number;
  height?: number;
}

export const PopulationPyramid: React.FC<PopulationPyramidProps> = ({
  data,
  width = 600,
  height = 400,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !data || data.length === 0) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll("*").remove();

    // Margins and dimensions
    const margin = { top: 20, right: 40, bottom: 40, left: 100 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    // Create SVG
    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height);

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Get unique age groups (in order they appear in data)
    const ageGroups: string[] = [];
    const ageGroupSet = new Set<string>();

    for (const d of data) {
      if (!ageGroupSet.has(d.age)) {
        ageGroups.push(d.age);
        ageGroupSet.add(d.age);
      }
    }

    // Separate male and female data
    const maleData = data.filter((d) => d.sex === "M");
    const femaleData = data.filter((d) => d.sex === "F");

    // Create maps for easy lookup
    const maleMap = new Map(maleData.map((d) => [d.age, d.value]));
    const femaleMap = new Map(femaleData.map((d) => [d.age, d.value]));

    // Find max value for scale
    const maxValue = Math.max(
      ...maleData.map((d) => d.value),
      ...femaleData.map((d) => d.value)
    );

    // Scales
    const yScale = d3
      .scaleBand()
      .domain(ageGroups)
      .range([0, chartHeight])
      .padding(0.2);

    const xScale = d3
      .scaleLinear()
      .domain([0, maxValue])
      .range([0, chartWidth / 2 - 10]); // Leave gap in middle

    // Create axes
    const yAxis = d3.axisLeft(yScale);

    g.append("g")
      .attr("class", "y-axis")
      .attr("transform", `translate(${chartWidth / 2}, 0)`)
      .call(yAxis)
      .selectAll("text")
      .style("font-size", "11px");

    // Male axis (left side) - reversed
    const xAxisLeft = d3
      .axisBottom(xScale)
      .ticks(5)
      .tickFormat((d) => String(d));

    g.append("g")
      .attr("class", "x-axis-left")
      .attr("transform", `translate(${chartWidth / 2 - chartWidth / 2}, ${chartHeight})`)
      .call(xAxisLeft)
      .selectAll("text")
      .style("font-size", "10px");

    // Female axis (right side)
    const xAxisRight = d3
      .axisBottom(xScale)
      .ticks(5)
      .tickFormat((d) => String(d));

    g.append("g")
      .attr("class", "x-axis-right")
      .attr("transform", `translate(${chartWidth / 2 + 10}, ${chartHeight})`)
      .call(xAxisRight)
      .selectAll("text")
      .style("font-size", "10px");

    // Male bars (left side)
    g.selectAll(".bar-male")
      .data(ageGroups)
      .enter()
      .append("rect")
      .attr("class", "bar-male")
      .attr("x", (d) => {
        const value = maleMap.get(d) || 0;
        return chartWidth / 2 - xScale(value);
      })
      .attr("y", (d) => yScale(d)!)
      .attr("width", (d) => xScale(maleMap.get(d) || 0))
      .attr("height", yScale.bandwidth())
      .attr("fill", "#3b82f6")
      .attr("opacity", 0.8)
      .on("mouseover", function (event, d) {
        d3.select(this).attr("opacity", 1);

        // Show tooltip
        const value = maleMap.get(d) || 0;
        g.append("text")
          .attr("class", "tooltip-male")
          .attr("x", chartWidth / 2 - xScale(value) - 5)
          .attr("y", yScale(d)! + yScale.bandwidth() / 2)
          .attr("text-anchor", "end")
          .attr("dominant-baseline", "middle")
          .style("font-size", "12px")
          .style("font-weight", "bold")
          .style("fill", "#1e40af")
          .text(value);
      })
      .on("mouseout", function () {
        d3.select(this).attr("opacity", 0.8);
        g.selectAll(".tooltip-male").remove();
      });

    // Female bars (right side)
    g.selectAll(".bar-female")
      .data(ageGroups)
      .enter()
      .append("rect")
      .attr("class", "bar-female")
      .attr("x", chartWidth / 2 + 10)
      .attr("y", (d) => yScale(d)!)
      .attr("width", (d) => xScale(femaleMap.get(d) || 0))
      .attr("height", yScale.bandwidth())
      .attr("fill", "#ec4899")
      .attr("opacity", 0.8)
      .on("mouseover", function (event, d) {
        d3.select(this).attr("opacity", 1);

        // Show tooltip
        const value = femaleMap.get(d) || 0;
        g.append("text")
          .attr("class", "tooltip-female")
          .attr("x", chartWidth / 2 + 10 + xScale(value) + 5)
          .attr("y", yScale(d)! + yScale.bandwidth() / 2)
          .attr("text-anchor", "start")
          .attr("dominant-baseline", "middle")
          .style("font-size", "12px")
          .style("font-weight", "bold")
          .style("fill", "#be185d")
          .text(value);
      })
      .on("mouseout", function () {
        d3.select(this).attr("opacity", 0.8);
        g.selectAll(".tooltip-female").remove();
      });

    // Labels
    g.append("text")
      .attr("x", chartWidth / 4)
      .attr("y", -5)
      .attr("text-anchor", "middle")
      .style("font-size", "12px")
      .style("font-weight", "600")
      .style("fill", "#3b82f6")
      .text("Masculino");

    g.append("text")
      .attr("x", chartWidth / 2 + 10 + chartWidth / 4)
      .attr("y", -5)
      .attr("text-anchor", "middle")
      .style("font-size", "12px")
      .style("font-weight", "600")
      .style("fill", "#ec4899")
      .text("Femenino");

    // Cleanup
    return () => {
      d3.select(svgRef.current).selectAll("*").remove();
    };
  }, [data, width, height]);

  return (
    <div className="population-pyramid-container" style={{ width: "100%", overflowX: "auto" }}>
      <svg ref={svgRef} style={{ display: "block", margin: "0 auto" }} />
    </div>
  );
};
