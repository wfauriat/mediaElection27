import { Route, Routes } from "react-router-dom";

import Dashboard from "@/routes/Dashboard";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
    </Routes>
  );
}
