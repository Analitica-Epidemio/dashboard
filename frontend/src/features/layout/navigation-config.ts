import {
  IconListDetails,
  IconFileUpload,
  IconSettings,
  IconFileText,
  IconTrendingUp,
  IconBuildingHospital,
  IconBook,
  IconDatabase,
  IconStethoscope,
  IconFlask,
  IconClipboardList,
  IconActivity,
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
    // SECCIÓN: VIGILANCIA (Nueva sección principal)
    {
      id: "header-vigilancia",
      title: "Vigilancia",
      type: "header",
    },
    {
      id: "dashboard-ejecutivo",
      title: "Dashboard",
      icon: IconActivity,
      url: "/dashboard",
      type: "link",
    },
    {
      id: "vigilancia-clinica",
      title: "Clínica",
      icon: IconStethoscope,
      url: "/dashboard/vigilancia/clinica",
      type: "link",
    },
    {
      id: "vigilancia-laboratorio",
      title: "Laboratorio",
      icon: IconFlask,
      url: "/dashboard/vigilancia/laboratorio",
      type: "link",
    },
    {
      id: "vigilancia-nominal",
      title: "Nominal",
      icon: IconClipboardList,
      url: "/dashboard/vigilancia/nominal",
      type: "link",
    },
    {
      id: "vigilancia-hospitalaria",
      title: "Hospitalaria",
      icon: IconBuildingHospital,
      url: "/dashboard/vigilancia/hospitalaria",
      type: "link",
    },

    // SECCIÓN: DATOS
    {
      id: "header-datos",
      title: "Datos",
      type: "header",
    },
    {
      id: "eventos",
      title: "Eventos",
      icon: IconListDetails,
      url: "/dashboard/eventos",
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
    {
      id: "boletines",
      title: "Boletines",
      icon: IconBook,
      url: "/dashboard/boletines",
      type: "link",
    },

    // SECCIÓN: SISTEMA
    {
      id: "header-sistema",
      title: "Sistema",
      type: "header",
    },
    {
      id: "catalogos",
      title: "Catálogos",
      icon: IconDatabase,
      url: "/dashboard/catalogos",
      type: "link",
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