import { BrowserRouter, Route, Routes } from "react-router";

import { ChroniclePage } from "./chronicle/ChroniclePage";
import { ChroniclesPage } from "./chronicles/ChroniclesPage";
import { KnowledgePage } from "./knowledge/KnowledgePage";
import { LatticePage } from "./lattice/LatticePage";
import { AppShell } from "./shell/AppShell";
import { StoryMapPage } from "./storyMap/StoryMapPage";
import { TryBeatPage } from "./tryBeat/TryBeatPage";

export function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<ChroniclesPage />} />
          <Route path="/chronicles/:chronicleId" element={<ChroniclePage />} />
          <Route path="/chronicles/:chronicleId/map" element={<StoryMapPage />} />
          <Route path="/chronicles/:chronicleId/map/knowledge" element={<StoryMapPage view="knowledge" />} />
          <Route path="/chronicles/:chronicleId/map/pacing" element={<StoryMapPage view="pacing" />} />
          <Route path="/chronicles/:chronicleId/map/evidence" element={<StoryMapPage view="evidence" />} />
          <Route path="/chronicles/:chronicleId/map/clues" element={<StoryMapPage view="clues" />} />
          <Route path="/chronicles/:chronicleId/lattice" element={<LatticePage />} />
          <Route path="/chronicles/:chronicleId/knowledge" element={<KnowledgePage />} />
          <Route path="/chronicles/:chronicleId/try" element={<TryBeatPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}
