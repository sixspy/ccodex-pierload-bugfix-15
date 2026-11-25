export function createApi(getToken, onUnauthorized) {
  async function req(path, options = {}) {
    const headers = Object.assign({ "Content-Type": "application/json" }, options.headers || {});
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(path, { ...options, headers });
    const text = await res.text();
    let body = null;
    try { body = text ? JSON.parse(text) : null; } catch { body = { detail: text }; }
    if (res.status === 401) onUnauthorized && onUnauthorized();
    if (!res.ok) {
      const detail = body && (body.detail || body.message);
      throw new Error(typeof detail === "string" ? detail : res.statusText);
    }
    return body;
  }
  return {
    dashboard: () => req("/api/dashboard"),
    bridges: () => req("/api/bridges"),
    bridge: (id) => req(`/api/bridges/${id}`),
    createBridge: (d) => req("/api/bridges", { method: "POST", body: JSON.stringify(d) }),
    lanes: (bridgeId) => req(bridgeId ? `/api/lanes?bridge_id=${bridgeId}` : "/api/lanes"),
    lane: (id) => req(`/api/lanes/${id}`),
    createLane: (d) => req("/api/lanes", { method: "POST", body: JSON.stringify(d) }),
    tickets: (st) => req(st ? `/api/tickets?status=${encodeURIComponent(st)}` : "/api/tickets"),
    ticket: (id) => req(`/api/tickets/${id}`),
    createTicket: (d) => req("/api/tickets", { method: "POST", body: JSON.stringify(d) }),
    overloads: (st) => req(st ? `/api/overloads?status=${encodeURIComponent(st)}` : "/api/overloads"),
    openOverload: (d) => req("/api/overloads/open", { method: "POST", body: JSON.stringify(d) }),
    closeOverload: (d) => req("/api/overloads/close", { method: "POST", body: JSON.stringify(d) }),
    rejectOverload: (d) => req("/api/overloads/reject", { method: "POST", body: JSON.stringify(d) }),
    gateReleases: () => req("/api/gate/releases"),
    releaseGate: (d) => req("/api/gate/release", { method: "POST", body: JSON.stringify(d) }),
    seals: () => req("/api/seals"),
    createSeal: (d) => req("/api/seals", { method: "POST", body: JSON.stringify(d) }),
    blList: () => req("/api/bl"),
    registerBl: (d) => req("/api/bl", { method: "POST", body: JSON.stringify(d) }),
    lineage: () => req("/api/lineage"),
    addLineage: (d) => req("/api/lineage", { method: "POST", body: JSON.stringify(d) }),
    reconcileAll: () => req("/api/reconcile"),
    reconcileOne: (code) => req(`/api/reconcile/${encodeURIComponent(code)}`),
    proofTicket: (code) => req(`/api/proof/ticket/${encodeURIComponent(code)}`),
    customsJobs: () => req("/api/customs/jobs"),
    customsStub: (d) => req("/api/customs-stub", { method: "POST", body: JSON.stringify(d) }),
    craneJobs: () => req("/api/crane/jobs"),
    craneStub: (d) => req("/api/crane-stub", { method: "POST", body: JSON.stringify(d) }),
    contention: () => req("/api/contention"),
  };
}
