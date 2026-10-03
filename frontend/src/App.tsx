import { BrowserRouter, Route, Routes } from "react-router";

import { ChroniclePage } from "./chronicle/ChroniclePage";
import { ChroniclesPage } from "./chronicles/ChroniclesPage";
import { LatticePage } from "./lattice/LatticePage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChroniclesPage />} />
        <Route path="/chronicles/:chronicleId" element={<ChroniclePage />} />
        <Route path="/chronicles/:chronicleId/lattice" element={<LatticePage />} />
      </Routes>
    </BrowserRouter>
  );
}
