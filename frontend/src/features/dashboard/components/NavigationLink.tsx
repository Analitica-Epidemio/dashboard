/**
 * Componente de enlace de navegación para agregar al menú principal
 * Permite acceso rápido al nuevo dashboard epidemiológico
 */

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Activity, BarChart3, TrendingUp } from 'lucide-react';

export const EpidemiologyNavigationCard: React.FC = () => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Análisis Epidemiológico Avanzado
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Dashboard completo con KPIs, alertas y visualizaciones especializadas 
            para vigilancia epidemiológica en tiempo real.
          </p>
        </div>
        <Activity className="h-8 w-8 text-blue-500 flex-shrink-0" />
      </div>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <div className="flex items-center gap-1">
            <BarChart3 className="h-4 w-4" />
            <span>7 Tipos de Análisis</span>
          </div>
          <div className="flex items-center gap-1">
            <TrendingUp className="h-4 w-4" />
            <span>KPIs en Tiempo Real</span>
          </div>
        </div>
        
        <Link href="/epidemiologia">
          <Button className="bg-blue-600 hover:bg-blue-700">
            Abrir Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
};