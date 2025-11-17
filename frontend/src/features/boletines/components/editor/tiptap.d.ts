/**
 * Type declarations for custom Tiptap extensions
 */

import '@tiptap/core';

// Tipos específicos para attrs de nodos personalizados
export interface DynamicChartAttrs {
  chartId?: number;
  chartCode?: string;
  queryType?: string;
  chartType?: string;
  title?: string;
  grupoIds?: string;
  eventoIds?: string;
  fechaDesde?: string;
  fechaHasta?: string;
}

export interface VariableAttrs {
  variableId?: string;
  variableKey?: string;
  variableLabel?: string;
  variableEmoji?: string;
  variableType?: 'basic' | 'stat' | 'chart';
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    variable: {
      /**
       * Insert a variable placeholder
       */
      insertVariable: (
        variableKey: string,
        variableLabel?: string,
        variableEmoji?: string,
        variableType?: 'basic' | 'stat' | 'chart'
      ) => ReturnType;
      /**
       * Set variable (alternative command name)
       */
      setVariable: (variableId: string) => ReturnType;
    };
    dynamicTable: {
      /**
       * Insert a dynamic table
       */
      insertDynamicTable: (attrs: {
        queryType?: string;
        title?: string;
      }) => ReturnType;
      /**
       * Set dynamic table (alternative command name)
       */
      setDynamicTable: (config: {
        queryType: string;
        title?: string;
      }) => ReturnType;
    };
    pageBreak: {
      /**
       * Insert a page break
       */
      insertPageBreak: () => ReturnType;
      /**
       * Set page break (alternative command name)
       */
      setPageBreak: () => ReturnType;
    };
    dynamicChart: {
      /**
       * Insert a dynamic chart
       */
      insertDynamicChart: (attrs: DynamicChartAttrs) => ReturnType;
      /**
       * Set dynamic chart config
       */
      setDynamicChart: (config: DynamicChartAttrs) => ReturnType;
    };
  }
}
