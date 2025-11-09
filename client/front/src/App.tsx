import { Route, Routes } from "react-router-dom";
import { IndexPage } from "./pages";
import Dashboard from "./pages/dashboard";
import MarketPage from "./pages/market";
import AssetPage from "./pages/asset";
import WarRoom from "./pages/war-room";
import CrashSimulator from "./pages/crash-simulator";

function App() {
  return (
    <Routes>
      <Route element={<IndexPage />} path="/" />
      <Route element={<WarRoom />} path="/war-room" />
      <Route element={<CrashSimulator />} path="/crash-simulator" />
      <Route element={<Dashboard />} path="/old-dashboard" />
      <Route element={<MarketPage />} path="/market" />
      <Route element={<AssetPage />} path="/asset/:symbol" />
    </Routes>
  );
}

export default App;
