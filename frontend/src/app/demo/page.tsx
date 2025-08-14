"use client";

import { $api } from "@/lib/api/client";
import type { components } from "@/lib/api/types";

type ErrorResponse = components["schemas"]["ErrorResponse"];

export default function DemoPage() {
  const { data, error, isPending } = $api.useQuery(
    "get",
    "/api/v1/hello"
  );

  if (isPending) return <div>Cargando...</div>;
  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-100 text-red-700 p-4 rounded">
          <p className="font-semibold">Error:</p>
          <p>{error.message || "Error al cargar datos"}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Demo API Client</h1>
      <div className="bg-gray-100 p-4 rounded">
        <p className="font-semibold">Mensaje:</p>
        <p>{data?.message}</p>
        <p className="font-semibold mt-2">Timestamp:</p>
        <p>{data?.timestamp}</p>
      </div>
    </div>
  );
}