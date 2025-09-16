/**
 * Print-optimized SSR Reports Page
 * Fetches data server-side, renders with client components
 */

import React from "react";
import { env } from "@/env";
import { PrintReportClient } from "./PrintReportClient";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";

interface PageProps {
  searchParams: {
    filters?: string;
    dateFrom?: string;
    dateTo?: string;
  };
}

interface FilterCombination {
  id: string;
  groupId: number | null;
  groupName?: string;
  eventIds: number[];
  eventNames?: string[];
  clasificaciones?: string[];
}

async function fetchReportData(
  combinations: FilterCombination[],
  dateRange: { from: string; to: string }
) {
  const apiHost = env.NEXT_PUBLIC_API_HOST;

  // Get session for authentication
  const session = await getServerSession(authOptions);
  const headers: HeadersInit = session?.accessToken
    ? { 'Authorization': `Bearer ${session.accessToken}` }
    : {};

  const processedCombinations = [];

  for (const combo of combinations) {
    try {
      const params = new URLSearchParams();
      if (combo.groupId) params.append("grupo_id", combo.groupId.toString());
      if (combo.eventIds?.[0])
        params.append("evento_id", combo.eventIds[0].toString());
      params.append("fecha_desde", dateRange.from);
      params.append("fecha_hasta", dateRange.to);
      if (combo.clasificaciones?.length) {
        combo.clasificaciones.forEach((c) =>
          params.append("clasificaciones", c)
        );
      }

      // Fetch indicators with authentication
      const indicadoresRes = await fetch(
        `${apiHost}/api/v1/charts/indicadores?${params.toString()}`,
        { cache: "no-store", headers }
      );
      const indicadores = await indicadoresRes.json();

      // Fetch charts with authentication
      const chartsRes = await fetch(
        `${apiHost}/api/v1/charts/dashboard?${params.toString()}`,
        { cache: "no-store", headers }
      );
      const chartsData = await chartsRes.json();

      processedCombinations.push({
        ...combo,
        indicadores,
        charts: chartsData.charts || [],
      });
    } catch (error) {
      console.error("Error fetching data for combination:", error);
      processedCombinations.push({
        ...combo,
        indicadores: {},
        charts: [],
      });
    }
  }

  return processedCombinations;
}

export default async function ReportsPrintPage({ searchParams }: PageProps) {
  let filterCombinations: FilterCombination[] = [];
  let dateRange = {
    from: searchParams.dateFrom || "",
    to: searchParams.dateTo || "",
  };

  if (searchParams.filters) {
    try {
      filterCombinations = JSON.parse(searchParams.filters);
    } catch (e) {
      console.error("Error parsing filters:", e);
    }
  }

  // Fetch data server-side
  const reportData = await fetchReportData(filterCombinations, dateRange);

  // Pass data to client component
  return (
    <PrintReportClient
      reportData={reportData}
      dateRange={dateRange}
    />
  );
}