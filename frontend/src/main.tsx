import "@fontsource-variable/cinzel";
import "@fontsource-variable/crimson-pro";
import "./theme/tokens.css";
import "./theme/global.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";

const root = document.getElementById("root");
if (!root) {
  throw new Error("index.html has no #root element");
}
createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
