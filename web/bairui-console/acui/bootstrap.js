import { startACUI } from "./client.js";

export function bootstrapACUI() {
  let acuiHost = document.getElementById("acui-host");
  if (!acuiHost) {
    acuiHost = document.createElement("div");
    acuiHost.id = "acui-host";
    document.body.appendChild(acuiHost);
  }

  if (!document.getElementById("acui-animations-css")) {
    const link = document.createElement("link");
    link.id = "acui-animations-css";
    link.rel = "stylesheet";
    link.href = "/console/acui/animations.css";
    document.head.appendChild(link);
  }

  if (window.BAIRUI_ENABLE_ACUI_WS !== true) return;
  const wsProto = location.protocol === "https:" ? "wss:" : "ws:";
  const wsHost = location.host || "localhost:8787";
  const wsUrl = `${wsProto}//${wsHost}/acui`;
  startACUI({ wsUrl, hostElement: acuiHost });
}

