import { BrowserRouter, Route, Routes } from "react-router";

import { ChroniclesPage } from "./chronicles/ChroniclesPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChroniclesPage />} />
      </Routes>
    </BrowserRouter>
  );
}
