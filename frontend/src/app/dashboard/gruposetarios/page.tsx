import { useState } from "react";

export default function RangosEdad() {
  const [rangos, setRangos] = useState([
    { desde: 0, hasta: "", unidad: "años" }
  ]);

  const unidades = ["días", "meses", "años"];

  const actualizarRango = (index, campo, valor) => {
    const nuevos = [...rangos];
    nuevos[index][campo] = valor;

    // Si cambió el límite "hasta", actualizamos el inicio del siguiente
    if (campo === "hasta" && index < rangos.length - 1) {
      nuevos[index + 1].desde = parseFloat(valor) || 0;
    }

    setRangos(nuevos);
  };

  const agregarRango = () => {
    const ultimo = rangos[rangos.length - 1];
    if (ultimo.hasta === "" || isNaN(ultimo.hasta)) return;

    setRangos([
      ...rangos,
      { desde: parseFloat(ultimo.hasta), hasta: "", unidad: "años" }
    ]);
  };

  const eliminarRango = (index) => {
    const nuevos = rangos.filter((_, i) => i !== index);
    if (nuevos.length === 0) nuevos.push({ desde: 0, hasta: "", unidad: "años" });
    setRangos(nuevos);
  };

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-bold">Definir rangos etarios</h2>

      {rangos.map((rango, index) => (
        <div key={index} className="flex items-center gap-3">
          <span className="w-10 text-right">{rango.desde}</span>
          <span>-</span>

          <input
            type="number"
            className="border rounded p-1 w-24"
            value={rango.hasta}
            placeholder={index === rangos.length - 1 ? "∞" : ""}
            disabled={index === rangos.length - 1 && !rango.hasta}
            onChange={(e) => actualizarRango(index, "hasta", e.target.value)}
          />

          <select
            className="border rounded p-1"
            value={rango.unidad}
            onChange={(e) => actualizarRango(index, "unidad", e.target.value)}
            disabled={rango.desde >= 1 && rango.unidad === "años"}
          >
            {unidades.map((u) => (
              <option
                key={u}
                value={u}
                disabled={rango.desde >= 1 && u === "días"}
              >
                {u}
              </option>
            ))}
          </select>

          {index === rangos.length - 1 ? (
            <button
              onClick={agregarRango}
              className="bg-green-500 text-white px-2 py-1 rounded"
            >
              +
            </button>
          ) : (
            <button
              onClick={() => eliminarRango(index)}
              className="bg-red-500 text-white px-2 py-1 rounded"
            >
              -
            </button>
          )}
        </div>
      ))}

      <pre className="bg-gray-100 p-2 rounded text-sm">
        {JSON.stringify(rangos, null, 2)}
      </pre>
    </div>
  );
}
