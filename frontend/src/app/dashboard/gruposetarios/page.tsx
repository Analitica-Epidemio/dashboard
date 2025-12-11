"use client";

import { useEffect, useState } from "react";

export default function GruposEtariosPage() {
  const [configs, setConfigs] = useState<any[]>([]);
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [rangos, setRangos] = useState([{ desde: 0, hasta: "", unidad: "años" }]);
  const [loading, setLoading] = useState(false);

  const API_URL = `${process.env.NEXT_PUBLIC_API_HOST}/api/v1/grupos_etarios`;

  const cargar = async () => {
    try {
      const res = await fetch(API_URL, { cache: "no-store" });
      if (!res.ok) throw new Error("Error al obtener datos");
      const data = await res.json();
      setConfigs(data);
    } catch (err) {
      console.error(err);
    }
  };
  
    const comparar = (h: number, u1: string, r2: number, d: string) => {
        if (u1 == "dias"){
            const v1 = math.round(h/30.4);
	}
        if (u1 == "años"){
            const v1 = h*12;
	}
        if (u1 == "meses"){
            const v1 = h;
	}
        if (u2 == "dias"){
            const v2 = math.round(d/30.4);
	}
        if (u2 == "años"){
            const v2 = d*12;
	}
        if (u1 == "meses"){
            const v2 = d;
	}
        if (v1 == v2){
            return 0;
	}
        if (v1 > v2){
            return 1;
	}
        return -1;
    } 
  
    const validar = () => {
        for(var _i = 0; _i < rangos.length; _i++){
            switch (comparar(rangos[i].hasta, rangos[i].unidad, rangos[i+1].desde, rangos[i+1].unidad)){
                case 0:
                    break;
                case 1:
                    return 1;
                case -1:
                    return -1;
        }
        return 0;
    }

  useEffect(() => {
    cargar();
  }, []);

  const crear = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const val = validar();
    if(val == 0){
        try {
          const payload = { nombre, descripcion, rangos };
          const res = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          if (!res.ok) throw new Error("Error al crear configuración");
          await cargar();
          setNombre("");
          setDescripcion("");
          setRangos([{ desde: 0, hasta: "", unidad: "años" }]);
        } catch (err) {
          console.error(err);
        } finally {
          setLoading(false);
        }
    }
    if (val == 1)
        throw new Error("Los rangos se superponen");
    if (val == -1)
        throw new Error("Los rangos no son continuos");
  };

  const eliminar = async (id: number) => {
    if (!confirm("¿Eliminar esta configuración?")) return;
    try {
      const res = await fetch(`${API_URL}/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Error al eliminar configuración");
      await cargar();
    } catch (err) {
      console.error(err);
    }
  };

  const actualizarRango = (index: number, field: string, value: any) => {
    const nuevos = [...rangos];
    nuevos[index][field] = value;

    // si se cambia "hasta", actualizar el "desde" del siguiente
    if (field === "hasta" && nuevos[index + 1]) {
      nuevos[index + 1].desde = parseFloat(value) || 0;
    }
    setRangos(nuevos);
  };

  const agregarRango = () => {
    const ultimo = rangos[rangos.length - 1];
    const nuevoDesde = parseFloat(ultimo.hasta) || 0;
    setRangos([...rangos, { desde: nuevoDesde, hasta: "", unidad: ultimo.unidad }]);
  };

  const eliminarRango = (index: number) => {
    const nuevos = rangos.filter((_, i) => i !== index);
    setRangos(nuevos);
  };

function unidadesPermitidas(desde: number, unidad: string) {
    if (unidad == "días")
        if (desde >= 365)
            return ["años"];
    if (unidad == "meses")
        if (desde >= 12)
            return ["años"];
    return ["días", "meses", "años"];
}


  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold mb-4">Configuraciones de Grupos Etarios</h1>

      <form onSubmit={crear} className="border p-4 rounded space-y-3">
        <h2 className="font-semibold">Nueva configuración</h2>

        <input
          type="text"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          placeholder="Nombre"
          className="border rounded p-2 w-full"
          required
        />

        <div className="space-y-2">
          <h3 className="font-medium">Rangos</h3>
            {rangos.map((r, i) => {
              const unidadesDisponibles = unidadesPermitidas(r.desde, r.unidad);

              // Si la unidad actual ya no está disponible, ajustarla automáticamente
              if (!unidadesDisponibles.includes(r.unidad)) {
                r.unidad = unidadesDisponibles[0];
              }

              return (
                <div key={i} className="flex items-center space-x-2">
                  <input
                    type="number"
                    value={r.desde}
                    readOnly
                    className="border p-2 w-20 rounded bg-gray-100"
                  />
                  <span>a</span>
                  <input
                    type="number"
                    value={r.hasta}
                    onChange={(e) => actualizarRango(i, "hasta", e.target.value)}
                    placeholder="hasta"
                    className="border p-2 w-20 rounded"
                  />

                  <select
                    value={r.unidad}
                    onChange={(e) => actualizarRango(i, "unidad", e.target.value)}
                    className="border p-2 rounded"
                  >
                    {unidadesDisponibles.map((u) => (
                      <option key={u} value={u}>
                        {u}
                      </option>
                    ))}
                  </select>

                  {i === rangos.length - 1 && (
                    <button
                      type="button"
                      onClick={agregarRango}
                      className="text-green-600 hover:text-green-800 font-bold text-lg"
                    >
                      +
                    </button>
                  )}
                  {rangos.length > 1 && (
                    <button
                      type="button"
                      onClick={() => eliminarRango(i)}
                      className="text-red-600 hover:text-red-800 font-bold text-lg"
                    >
                      -
                    </button>
                  )}
                </div>
              );
            })}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          {loading ? "Guardando..." : "Guardar configuración"}
        </button>
      </form>

      <hr className="my-6" />

      {configs.length === 0 ? (
        <p className="text-gray-500">No hay configuraciones guardadas.</p>
      ) : (
        <div className="space-y-3">
          {configs.map((c) => (
            <div key={c.id} className="border p-3 rounded flex justify-between items-start">
              <div>
                <h3 className="font-semibold">{c.nombre}</h3>
                <p className="text-sm text-gray-500">{c.descripcion}</p>
                <ul className="mt-2 text-sm text-gray-700">
                  {c.rangos.map((r: any, i: number) => (
                    <li key={i}>
                      {r.desde} – {r.hasta ?? "+"} {r.unidad}
                    </li>
                  ))}
                </ul>
              </div>
              <button
                onClick={() => eliminar(c.id)}
                className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600"
              >
                Eliminar
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
