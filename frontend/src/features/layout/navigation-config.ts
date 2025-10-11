import {
  IconDashboard,
  IconListDetails,
  IconFileUpload,
  IconSettings,
  IconChartLine,
  IconUsers,
  IconMap,
  IconFileText,
} from "@tabler/icons-react";

export interface NavItem {
  id: string;
  title: string;
  icon: React.ElementType;
  url: string;
  badge?: string;
}

export interface UserData {
  name: string;
  email: string;
  avatar?: string;
}

export const navigationConfig = {
  navMain: [
    {
      id: "dashboard",
      title: "Tablero",
      icon: IconDashboard,
      url: "/dashboard",
    },
    {
      id: "eventos",
      title: "Eventos",
      icon: IconListDetails,
      url: "/dashboard/eventos",
    },
    {
      id: "personas",
      title: "Personas",
      icon: IconUsers,
      url: "/dashboard/personas",
    },
    {
      id: "mapa",
      title: "Mapa",
      icon: IconMap,
      url: "/dashboard/mapa",
    },
    {
      id: "archivos",
      title: "Subir Archivo",
      icon: IconFileUpload,
      url: "/dashboard/archivos/subir",
    },
    {
      id: "estrategias",
      title: "Estrategias",
      icon: IconChartLine,
      url: "/dashboard/estrategias",
    },
    {
      id: "reportes",
      title: "Reportes",
      icon: IconFileText,
      url: "/dashboard/reportes",
    },
    {
      id: "settings",
      title: "Configuración",
      icon: IconSettings,
      url: "/dashboard/settings/reportes",
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