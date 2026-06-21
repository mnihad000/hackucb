import type { RouteObject } from "react-router-dom";
import LandingPage from "../pages/LandingPage";
import DashboardPage from "../pages/DashboardPage";
import InvestigationPage from "../pages/InvestigationPage";

export const appRoutes: RouteObject[] = [
  {
    path: "/",
    element: <LandingPage />,
  },
  {
    path: "/dashboard",
    element: <DashboardPage />,
  },
  {
    path: "/investigation/:id",
    element: <InvestigationPage />,
  },
];
