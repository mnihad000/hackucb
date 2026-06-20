import type { RouteObject } from "react-router-dom";
import DashboardPage from "../pages/DashboardPage";
import InvestigationPage from "../pages/InvestigationPage";

export const appRoutes: RouteObject[] = [
  {
    path: "/",
    element: <DashboardPage />,
  },
  {
    path: "/investigation/:id",
    element: <InvestigationPage />,
  },
];
