import { Route, Routes } from "react-router-dom";

import { IndexPage } from "./pages";
import Dashboard from "./pages/dashboard";
import MarketPage from "./pages/market";
import AssetPage from "./pages/asset";

function App() {
  return (
    <Routes>
      <Route element={<IndexPage />} path="/" />
      <Route element={<Dashboard />} path="/old-dashboard" />
      <Route element={<MarketPage />} path="/market" />
      <Route element={<AssetPage />} path="/asset/:symbol" />
    </Routes>
  );
}

export default App;
