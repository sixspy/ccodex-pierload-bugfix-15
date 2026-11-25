import { createApi } from "./api.js";
import { dashboardViewTemplate } from "./views/dashboard_view.js";
import { bridgesViewTemplate } from "./views/bridges_view.js";
import { lanesViewTemplate } from "./views/lanes_view.js";
import { ticketsViewTemplate } from "./views/tickets_view.js";
import { overloadViewTemplate } from "./views/overload_view.js";
import { gateViewTemplate } from "./views/gate_view.js";
import { sealViewTemplate } from "./views/seal_view.js";
import { blViewTemplate } from "./views/bl_view.js";
import { lineageViewTemplate } from "./views/lineage_view.js";
import { reconcileViewTemplate } from "./views/reconcile_view.js";
import { stubsViewTemplate } from "./views/stubs_view.js";

const { createApp, ref, computed, watch, onMounted } = Vue;

createApp({
  setup() {
    const token = ref(localStorage.getItem("pierload_token") || "");
    const user = ref(localStorage.getItem("pierload_user") || "");
    const username = ref("admin");
    const password = ref("admin123");
    const err = ref("");
    const actionErr = ref("");
    const actionOk = ref("");
    const tab = ref(0);
    const nav = ["总览","地磅","车道","过磅","超重","放行","快照","提单","血缘","对账","空桩"];

    const dash = ref({});
    const bridges = ref([]);
    const lanes = ref([]);
    const tickets = ref([]);
    const overloads = ref([]);
    const gateReleases = ref([]);
    const seals = ref([]);
    const blList = ref([]);
    const lineageEdges = ref([]);
    const customsJobs = ref([]);
    const craneJobs = ref([]);
    const bridgeDetail = ref(null);
    const ticketDetail = ref(null);
    const reconOne = ref(null);
    const reconAllItems = ref([]);
    const proofOne = ref(null);
    const reconCode = ref("BL-2026-0101");
    const proofCode = ref("WT-LN-N-01-IN-001");

    const bridgeForm = ref({
      bridge_code: "WB-NEW-01", pier_zone: "北岸", name: "新建地磅",
      max_gross_t: 60, axle_limit: 6,
    });
    const laneForm = ref({
      lane_code: "LN-NEW-IN", bridge_id: 1, direction: "进闸",
      overload_threshold_t: 40, side_lane_ref: "旁路丁",
    });
    const ticketForm = ref({
      lane_id: 1, bl_ref: "BL-2026-0101", vehicle_plate: "沪A·试0001",
      ticket_code: "", axles_json: '[{"axle":1,"w":9},{"axle":2,"w":11},{"axle":3,"w":10}]',
    });
    const overloadOpenForm = ref({ ticket_id: 0, side_lane_note: "" });
    const gateForm = ref({ ticket_id: 0, officer: "闸口值班" });
    const sealForm = ref({ ticket_id: 0, manifest: "" });
    const blForm = ref({
      bl_code: "BL-NEW-01", cargo_desc: "件杂货", declared_gross_t: 30, vessel_voyage: "试航/001",
    });
    const lineageForm = ref({
      from_ticket_id: 1, to_ticket_id: 2, edge_type: "二次过磅", detail: "驳载后重检",
    });
    const customsForm = ref({ bl_code: "BL-2026-0101", row_count: 1 });
    const craneForm = ref({ berth_slot: "B-09", ticket_id: null });

    function logout() {
      token.value = "";
      user.value = "";
      localStorage.removeItem("pierload_token");
      localStorage.removeItem("pierload_user");
    }
    const api = createApi(() => token.value, () => logout());

    const adjudicableTickets = computed(() =>
      tickets.value.filter((t) => t.status !== "作废" && t.status !== "已封闸")
    );
    const releasableTickets = computed(() =>
      tickets.value.filter((t) => t.status === "已裁定")
    );
    // 第30号：放行页灰因同源可见——旁路挂起票（bypass_pending 派生位）
    const bypassBlockedTickets = computed(() =>
      tickets.value.filter((t) => t.bypass_pending || t.status === "旁路挂起")
    );
    const sealableTickets = computed(() =>
      tickets.value.filter((t) => ["已裁定","已放行"].includes(t.status))
    );

    function fmtT(n) {
      if (n == null || n === "") return "—";
      return Number(n).toFixed(2) + "t";
    }
    function ticketClass(s) {
      if (!s) return "muted";
      if (s.includes("挂起")) return "fail";
      if (s.includes("放行") || s.includes("裁定")) return "pass";
      if (s.includes("封闸")) return "warn";
      return "muted";
    }
    function shortText(t) {
      if (!t) return "";
      const s = String(t);
      return s.slice(0, 52) + (s.length > 52 ? "…" : "");
    }
    function clearFlash() { actionErr.value = ""; actionOk.value = ""; }
    function flashOk(m) { actionOk.value = m; actionErr.value = ""; }
    function flashErr(e) { actionErr.value = e.message || String(e); actionOk.value = ""; }

    async function login() {
      err.value = "";
      const r = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.value, password: password.value }),
      });
      const j = await r.json();
      if (!r.ok) { err.value = j.detail || "登录失败"; return; }
      token.value = j.token;
      user.value = j.username;
      localStorage.setItem("pierload_token", j.token);
      localStorage.setItem("pierload_user", j.username);
      await refresh();
    }

    async function refresh() {
      if (!token.value) return;
      clearFlash();
      try {
        const [d, br, ln, tk, ov, gr, sl, bl, lg, cj, cj2] = await Promise.all([
          api.dashboard(), api.bridges(), api.lanes(), api.tickets(), api.overloads(),
          api.gateReleases(), api.seals(), api.blList(), api.lineage(),
          api.customsJobs(), api.craneJobs(),
        ]);
        dash.value = d || {};
        bridges.value = br.items || [];
        lanes.value = ln.items || [];
        tickets.value = tk.items || [];
        overloads.value = ov.items || [];
        gateReleases.value = gr.items || [];
        seals.value = sl.items || [];
        blList.value = bl.items || [];
        lineageEdges.value = lg.items || [];
        customsJobs.value = cj.items || [];
        craneJobs.value = cj2.items || [];
        if (bridges.value.length) {
          laneForm.value.bridge_id = laneForm.value.bridge_id || bridges.value[0].id;
        }
        if (lanes.value.length) {
          ticketForm.value.lane_id = ticketForm.value.lane_id || lanes.value[0].id;
        }
        if (releasableTickets.value.length) {
          gateForm.value.ticket_id = releasableTickets.value[0].id;
        }
        if (sealableTickets.value.length) {
          sealForm.value.ticket_id = sealableTickets.value[0].id;
        }
        if (adjudicableTickets.value.length) {
          overloadOpenForm.value.ticket_id = adjudicableTickets.value[0].id;
        }
      } catch (e) { flashErr(e); }
    }

    async function createBridge() {
      clearFlash();
      try { await api.createBridge(bridgeForm.value); flashOk("地磅已登记"); await refresh(); }
      catch (e) { flashErr(e); }
    }
    async function loadBridgeDetail(id) { bridgeDetail.value = await api.bridge(id); }
    async function createLane() {
      clearFlash();
      try { await api.createLane(laneForm.value); flashOk("车道已开通"); await refresh(); }
      catch (e) { flashErr(e); }
    }
    async function createTicket() {
      clearFlash();
      try {
        const axles = JSON.parse(ticketForm.value.axles_json || "[]");
        const payload = {
          lane_id: ticketForm.value.lane_id,
          bl_ref: ticketForm.value.bl_ref,
          vehicle_plate: ticketForm.value.vehicle_plate,
          axle_weights: axles,
        };
        if (ticketForm.value.ticket_code) payload.ticket_code = ticketForm.value.ticket_code;
        const r = await api.createTicket(payload);
        flashOk(`过磅完成：${r.status}${r.overload ? "（超重）" : ""}`);
        await refresh();
      } catch (e) { flashErr(e); }
    }
    async function loadTicketDetail(id) { ticketDetail.value = await api.ticket(id); }
    function selectTicket() {}
    async function openOverload() {
      clearFlash();
      try {
        await api.openOverload(overloadOpenForm.value);
        flashOk("挂起已开"); await refresh();
      } catch (e) { flashErr(e); }
    }
    async function closeOverload(holdId) {
      clearFlash();
      try {
        const r = await api.closeOverload({ hold_id: holdId, note: "前端驳回回态" });
        if (r.ticket_adjudicated && r.ticket_status === "已裁定") {
          flashOk(`驳回成功，主票状态已回写为「${r.ticket_status}」，旁路位抹除`);
        } else {
          flashOk(`挂起已闭，票态=${r.ticket_status || "仍有开放挂起"}`);
        }
        await refresh();
      } catch (e) { flashErr(e); }
    }
    async function releaseGate() {
      clearFlash();
      try {
        await api.releaseGate(gateForm.value);
        flashOk("已放行"); await refresh();
      } catch (e) { flashErr(e); }
    }
    async function createSeal() {
      clearFlash();
      try {
        const p = { ticket_id: sealForm.value.ticket_id };
        if (sealForm.value.manifest) p.manifest = sealForm.value.manifest;
        const r = await api.createSeal(p);
        flashOk(`快照 闸代${r.generation}`); await refresh();
      } catch (e) { flashErr(e); }
    }
    async function registerBl() {
      clearFlash();
      try { await api.registerBl(blForm.value); flashOk("提单已登记"); await refresh(); }
      catch (e) { flashErr(e); }
    }
    async function addLineage() {
      clearFlash();
      try { await api.addLineage(lineageForm.value); flashOk("血缘边已记"); await refresh(); }
      catch (e) { flashErr(e); }
    }
    async function loadReconcile() {
      clearFlash();
      try { reconOne.value = await api.reconcileOne(reconCode.value); }
      catch (e) { flashErr(e); }
    }
    async function loadAllReconcile() {
      clearFlash();
      try { reconAllItems.value = (await api.reconcileAll()).items || []; }
      catch (e) { flashErr(e); }
    }
    async function loadProof() {
      clearFlash();
      try { proofOne.value = await api.proofTicket(proofCode.value); }
      catch (e) { flashErr(e); }
    }
    async function enqueueCustoms() {
      clearFlash();
      try { await api.customsStub(customsForm.value); flashOk("海关空桩入队"); await refresh(); }
      catch (e) { flashErr(e); }
    }
    async function enqueueCrane() {
      clearFlash();
      try { await api.craneStub(craneForm.value); flashOk("岸桥空桩入队"); await refresh(); }
      catch (e) { flashErr(e); }
    }

    onMounted(() => {
      if (token.value) refresh();
    });

    return {
      token, user, username, password, err, actionErr, actionOk, tab, nav,
      dash, bridges, lanes, tickets, overloads, gateReleases, seals, blList,
      lineageEdges, customsJobs, craneJobs, bridgeDetail, ticketDetail,
      reconOne, reconAllItems, proofOne, reconCode, proofCode,
      bridgeForm, laneForm, ticketForm, overloadOpenForm, gateForm, sealForm,
      blForm, lineageForm, customsForm, craneForm,
      adjudicableTickets, releasableTickets, bypassBlockedTickets, sealableTickets,
      login, logout, refresh,
      fmtT, ticketClass, shortText,
      createBridge, loadBridgeDetail, createLane, createTicket, loadTicketDetail, selectTicket,
      openOverload, closeOverload, releaseGate, createSeal, registerBl, addLineage,
      loadReconcile, loadAllReconcile, loadProof, enqueueCustoms, enqueueCrane,
    };
  },
  template: `
    <div v-if="!token" class="login-hero">
      <div class="login-card">
        <h1>港口过磅闸口</h1>
        <p class="sub">过磅票入闸后裁定超重才放行，驳回进旁路挂起，闸代快照与提单册对账。</p>
        <label>账号</label><input v-model="username"/>
        <label>密码</label><input v-model="password" type="password"/>
        <button @click="login">登录</button>
        <p v-if="err" class="err">{{ err }}</p>
      </div>
    </div>
    <div v-else class="harbor-shell">
      <header class="harbor-top">
        <div style="display:flex;flex-wrap:wrap;align-items:flex-start;gap:16px;width:100%">
          <div>
            <h1>港口过磅闸口</h1>
            <p class="tagline">数据工程 · 港区地磅闸口裁定</p>
          </div>
          <div class="stat-strip">
            <span class="stat-pill">超重<strong>{{ dash.open_overloads ?? 0 }}</strong></span>
            <span class="stat-pill">旁路<strong>{{ dash.side_pending ?? 0 }}</strong></span>
            <span class="stat-pill">在港票<strong>{{ dash.tickets ?? 0 }}</strong></span>
          </div>
          <div class="top-actions">
            <span>{{ user }}</span>
            <button @click="refresh">刷新</button>
            <button @click="logout">退出</button>
          </div>
        </div>
      </header>
      <nav class="tab-strip">
        <button v-for="(n,i) in nav" :key="n" :class="{active: tab===i}" @click="tab=i">{{ n }}</button>
      </nav>
      <main class="harbor-main">
        <p v-if="actionErr" class="action-err">{{ actionErr }}</p>
        <p v-if="actionOk" class="ok-msg">{{ actionOk }}</p>
        <div v-show="tab===0">${dashboardViewTemplate}</div>
        <div v-show="tab===1">${bridgesViewTemplate}</div>
        <div v-show="tab===2">${lanesViewTemplate}</div>
        <div v-show="tab===3">${ticketsViewTemplate}</div>
        <div v-show="tab===4">${overloadViewTemplate}</div>
        <div v-show="tab===5">${gateViewTemplate}</div>
        <div v-show="tab===6">${sealViewTemplate}</div>
        <div v-show="tab===7">${blViewTemplate}</div>
        <div v-show="tab===8">${lineageViewTemplate}</div>
        <div v-show="tab===9">${reconcileViewTemplate}</div>
        <div v-show="tab===10">${stubsViewTemplate}</div>
      </main>
    </div>
  `,
}).mount("#app");
