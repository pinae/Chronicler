import { BrowserRouter, Route, Routes } from "react-router";

import { ChroniclePage } from "./chronicle/ChroniclePage";
import { ChroniclesPage } from "./chronicles/ChroniclesPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChroniclesPage />} />
        <Route path="/chronicles/:chronicleId" element={<ChroniclePage />} />
      </Routes>
    </BrowserRouter>
  );
}
