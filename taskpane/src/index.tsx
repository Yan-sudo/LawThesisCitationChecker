import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

/* Office.js calls this once the host application is ready */
Office.onReady(() => {
  const container = document.getElementById("root")!;
  createRoot(container).render(<App />);
});
