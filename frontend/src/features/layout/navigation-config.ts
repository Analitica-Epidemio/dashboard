import {
  IconDashboard,
  IconListDetails,
  IconFileUpload,
  IconSettings,
  IconUsers,
  IconMap,
  IconFileText,
  IconHome,
  IconTrendingUp,
  IconBuildingHospital,
} from "@tabler/icons-react";

export interface NavItem {
  id: string;
  title: string;
  icon?: React.ElementType;
  url?: string;
  badge?: string;
  type?: "separator" | "link" | "header";
}

export interface UserData {
  name: string;
  email: string;
  avatar?: string;
}

export const navigationConfig = {
  // Acción primaria (fuera del sidebar, en header)
  primaryAction: {
    id: "upload",
    title: "Subir Archivo",
    icon: IconFileUpload,
    url: "/dashboard/archivos/subir",
  },

  navMain: [
    // SECCIÓN: DATOS
    {
      id: "header-datos",
      title: "Datos",
      type: "header",
    },
    {
      id: "dashboard",
      title: "Resumen",
      icon: IconDashboard,
      url: "/dashboard",
      type: "link",
    },
    {
      id: "eventos",
      title: "Eventos",
      icon: IconListDetails,
      url: "/dashboard/eventos",
      type: "link",
    },
    {
      id: "personas",
      title: "Personas",
      icon: IconUsers,
      url: "/dashboard/personas",
      type: "link",
    },
    {
      id: "establecimientos",
      title: "Establecimientos",
      icon: IconBuildingHospital,
      url: "/dashboard/establecimientos",
      type: "link",
    },
    {
      id: "domicilios",
      title: "Domicilios",
      icon: IconHome,
      url: "/dashboard/domicilios",
      type: "link",
    },

    // SECCIÓN: ANÁLISIS
    {
      id: "header-analisis",
      title: "Análisis",
      type: "header",
    },
    {
      id: "mapa",
      title: "Mapa",
      icon: IconMap,
      url: "/dashboard/mapa",
      type: "link",
    },
    {
      id: "analytics",
      title: "Analytics",
      icon: IconTrendingUp,
      url: "/dashboard/analytics",
      type: "link",
    },
    {
      id: "reportes",
      title: "Reportes",
      icon: IconFileText,
      url: "/dashboard/reportes",
      type: "link",
    },

    // SECCIÓN: SISTEMA
    {
      id: "header-sistema",
      title: "Sistema",
      type: "header",
    },
    {
      id: "settings",
      title: "Configuración",
      icon: IconSettings,
      url: "/dashboard/configuracion",
      type: "link",
    },
  ] as NavItem[],

  appName: "Epidemiología",
};

export function getNavigationItems() {
  return navigationConfig.navMain;
}

export function getAppName() {
  return navigationConfig.appName;
}