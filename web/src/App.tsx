import { DashboardPage } from './features/dashboard/components/DashboardPage';
import { useDashboardData } from './features/dashboard/use-dashboard-data';

function App() {
  const dashboardState = useDashboardData();

  return (
    <DashboardPage
      data={dashboardState.data}
      uiState={dashboardState.uiState}
      controls={dashboardState.controls}
    />
  );
}

export default App;
