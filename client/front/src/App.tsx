import { Route, Routes } from "react-router-dom";
import { IndexPage } from "./pages";
import Dashboard from "./pages/dashboard";

function App() {
  return (
    <Routes>
      <Route element={<IndexPage />} path="/" />
      <Route element={<Dashboard />} path="/old-dashboard" />
      <Route element={<div className="container mx-auto px-4 py-6"><h1 className="text-2xl font-bold">Asset Detail - Coming Soon</h1></div>} path="/asset/:symbol" />
      <Route element={<div className="container mx-auto px-4 py-6"><h1 className="text-2xl font-bold">Market - Coming Soon</h1></div>} path="/market" />
    </Routes>
  );
}

export default App;
