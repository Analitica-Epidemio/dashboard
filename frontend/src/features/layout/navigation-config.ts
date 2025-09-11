import {
  IconDashboard,
  IconListDetails,
  IconFileUpload,
  IconSettings,
  IconChartLine,
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
      id: "archivos",
      title: "Subir Archivo",
      icon: IconFileUpload,
      url: "/dashboard/archivos/subir",
    },
    {
      id: "charts",
      title: "Charts",
      icon: IconChartLine,
      url: "/dashboard/charts",
    },
    {
      id: "estrategias",
      title: "Estrategias",
      icon: IconSettings,
      url: "/dashboard/estrategias",
    },
  ] as NavItem[],
  
  user: {
    name: "Usuario",
    email: "usuario@epidemio.com",
    avatar: "/avatars/default.jpg",
  } as UserData,
  
  appName: "Epidemiología",
};

export function getNavigationItems() {
  return navigationConfig.navMain;
}

export function getUserData() {
  return navigationConfig.user;
}

export function getAppName() {
  return navigationConfig.appName;
}