"use client"

import { useState } from "react";
import { crearConfiguracion } from "@/api/v1/grupos_etarios/service";
import SelectorEdad from "./SelectorEdad";

export default function RangosForm({ onCreate }: { onCreate: () => void }) {
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [rangos, setRangos] = useState([{ desde: 0, hasta: "", unidad: "años" }]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = { nombre, descripcion, rangos };
      await crearConfiguracion(payload);
      onCreate();
      setNombre("");
      setDescripcion("");
      setRangos([{ desde: 0, hasta: "", unidad: "años" }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border rounded space-y-3">
      <h2 className="font-bold text-lg">Nueva configuración</h2>

      <div className="space-y-2">
        <input
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          placeholder="Nombre"
          className="border rounded p-2 w-full"
          required
        />
        <textarea
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          placeholder="Descripción"
          className="border rounded p-2 w-full"
        />
      </div>

      <RangosEdad rangos={rangos} setRangos={setRangos} />

      <button
        type="submit"
        disabled={loading}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        {loading ? "Guardando..." : "Guardar configuración"}
      </button>
    </form>
  );
}
