"""生成 pierload 前端（港口琥珀石板主题）。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FE = ROOT / "frontend"


def w(rel: str, text: str) -> None:
    p = FE / rel if not rel.startswith("frontend") else ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.lstrip("\n"), encoding="utf-8")


def main() -> None:
    w(
        "index.html",
        """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>港口过磅闸口</title>
<link rel="stylesheet" href="/static/css/app.css"/>
<script src="/static/vue.global.prod.js"></script>
</head>
<body>
<div id="app"></div>
<noscript><p class="noscript">需要启用 JavaScript</p></noscript>
<script type="module" src="/static/js/app.js"></script>
</body>
</html>
""",
    )

    w("css/app.css", CSS)

    views = {
        "dashboard_view.js": DASH,
        "bridges_view.js": BRIDGES,
        "lanes_view.js": LANES,
        "tickets_view.js": TICKETS,
        "overload_view.js": OVERLOAD,
        "gate_view.js": GATE,
        "seal_view.js": SEAL,
        "bl_view.js": BL,
        "lineage_view.js": LINEAGE,
        "reconcile_view.js": RECON,
        "stubs_view.js": STUBS,
    }
    for name, body in views.items():
        w(f"js/views/{name}", body)

    w("js/api.js", API_JS)
    w("js/app.js", APP_JS)
    print("frontend generated at", FE)


CSS = r"""
/* 港口过磅闸口：石板色 + 琥珀警示 + 海港蓝顶栏（非绿侧栏克隆） */
:root {
  --bg-slate: #1a2332;
  --bg-panel: #243044;
  --bg-panel-2: #2d3a52;
  --harbor: #4a7ab8;
  --harbor-dim: #35629a;
  --amber: #e8a317;
  --amber-dim: #c4840f;
  --text: #eef2f7;
  --text-dim: #9aa8bc;
  --warn: #f0b429;
  --bad: #e76f51;
  --ok: #52b788;
  --line: #3d4f6a;
  --shadow: 0 14px 40px rgba(0, 0, 0, 0.42);
  --font-ui: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-mono: "Cascadia Mono", "Consolas", monospace;
}
* { box-sizing: border-box; }
html, body { margin: 0; min-height: 100%; }
body {
  font-family: var(--font-ui);
  color: var(--text);
  background: linear-gradient(165deg, #2a3d56 0%, var(--bg-slate) 45%, #141b26 100%);
}
.noscript { margin: 24px; padding: 16px; background: #4a2030; color: #fecaca; }
.login-hero {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px;
  background:
    radial-gradient(circle at 20% 10%, rgba(74, 122, 184, 0.35), transparent 45%),
    radial-gradient(circle at 80% 90%, rgba(232, 163, 23, 0.2), transparent 40%);
}
.login-card {
  width: min(480px, 100%);
  background: var(--bg-panel);
  border: 1px solid var(--harbor-dim);
  border-top: 4px solid var(--amber);
  padding: 32px;
  box-shadow: var(--shadow);
}
.login-card h1 { margin: 0 0 8px; color: var(--harbor); font-size: 28px; letter-spacing: 0.12em; }
.login-card .sub { color: var(--text-dim); font-size: 13px; line-height: 1.6; margin-bottom: 20px; }
.login-card label { display: block; font-size: 12px; color: var(--text-dim); margin: 12px 0 4px; }
.login-card input {
  width: 100%; padding: 10px 12px; border: 1px solid var(--line);
  background: var(--bg-slate); color: var(--text); border-radius: 4px;
}
.login-card button {
  margin-top: 20px; width: 100%; padding: 12px; border: none;
  background: linear-gradient(90deg, var(--harbor-dim), var(--harbor));
  color: #fff; font-weight: 600; cursor: pointer; border-radius: 4px;
}
.err { color: var(--bad); margin-top: 12px; font-size: 13px; }
.harbor-shell { min-height: 100vh; display: flex; flex-direction: column; }
.harbor-top {
  padding: 16px 24px;
  background: linear-gradient(90deg, #1e3a5f, #2d4a73 55%, #1a2332);
  border-bottom: 2px solid var(--amber-dim);
  box-shadow: var(--shadow);
}
.harbor-top h1 { margin: 0; font-size: 24px; color: #f5e6c8; letter-spacing: 0.1em; }
.harbor-top .tagline { color: var(--text-dim); font-size: 12px; margin-top: 4px; }
.stat-strip {
  display: flex; flex-wrap: wrap; gap: 12px; margin-top: 14px;
}
.stat-pill {
  padding: 8px 14px; background: rgba(0,0,0,0.25); border: 1px solid var(--line);
  border-radius: 20px; font-size: 12px;
}
.stat-pill strong { color: var(--amber); margin-left: 6px; font-family: var(--font-mono); }
.top-actions { margin-left: auto; display: flex; gap: 8px; align-items: center; font-size: 13px; }
.top-actions button {
  border: 1px solid var(--harbor); background: transparent; color: var(--text);
  padding: 6px 12px; cursor: pointer; border-radius: 4px;
}
.tab-strip {
  display: flex; flex-wrap: wrap; gap: 6px; padding: 12px 24px;
  background: var(--bg-panel); border-bottom: 1px solid var(--line);
}
.tab-strip button {
  border: 1px solid transparent; background: transparent; color: var(--text-dim);
  padding: 8px 14px; cursor: pointer; border-radius: 6px; font-size: 13px;
}
.tab-strip button:hover { color: var(--text); background: rgba(255,255,255,0.04); }
.tab-strip button.active {
  color: var(--amber); border-color: var(--amber-dim);
  background: var(--bg-panel-2);
}
.harbor-main { flex: 1; padding: 18px 24px 48px; overflow: auto; }
.panel {
  background: var(--bg-panel); border: 1px solid var(--line);
  border-radius: 8px; padding: 16px 18px; box-shadow: var(--shadow);
}
.panel h2 { margin: 0 0 6px; font-size: 18px; color: var(--harbor); }
.panel .hint { color: var(--text-dim); font-size: 13px; margin: 0 0 14px; line-height: 1.55; }
.form-row {
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-bottom: 10px;
}
.form-row label { display: block; font-size: 11px; color: var(--text-dim); margin-bottom: 4px; }
.form-row input, .form-row select, textarea {
  width: 100%; padding: 8px 10px; border: 1px solid var(--line);
  background: var(--bg-slate); color: var(--text); border-radius: 4px; font-size: 14px;
}
textarea { min-height: 80px; font-family: var(--font-mono); font-size: 12px; }
.actions { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 14px; }
.actions button, .mini-btn {
  border: none; background: var(--amber); color: #1a2332; padding: 8px 14px;
  font-size: 13px; cursor: pointer; border-radius: 4px; font-weight: 600;
}
.actions button.secondary, button.secondary {
  background: transparent; border: 1px solid var(--line); color: var(--text); font-weight: 500;
}
.mini-btn { padding: 4px 8px; font-size: 11px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th, .data-table td {
  border-bottom: 1px solid var(--line); padding: 8px 6px; text-align: left;
}
.data-table th { color: var(--harbor-dim); font-size: 11px; letter-spacing: 0.05em; }
.data-table tr:hover { background: rgba(74, 122, 184, 0.08); }
.badge {
  display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px;
  background: var(--bg-slate); border: 1px solid var(--line);
}
.badge.pass { border-color: var(--ok); color: var(--ok); }
.badge.fail { border-color: var(--bad); color: var(--bad); }
.badge.warn { border-color: var(--warn); color: var(--warn); }
.badge.muted { color: var(--text-dim); }
.detail-box {
  margin-top: 14px; padding: 12px; background: var(--bg-slate);
  border: 1px dashed var(--line); border-radius: 6px; font-size: 13px;
}
.ok-msg, .action-err {
  margin-bottom: 10px; padding: 8px 12px; border-radius: 4px; font-size: 13px;
}
.ok-msg { background: rgba(82, 183, 136, 0.15); color: #b7e4c7; border: 1px solid var(--ok); }
.action-err { background: rgba(231, 111, 81, 0.15); color: #fecaca; border: 1px solid var(--bad); }
.grid-2 { display: grid; grid-template-columns: 1.05fr 1fr; gap: 16px; }
@media (max-width: 900px) { .grid-2 { grid-template-columns: 1fr; } }
.mono { font-family: var(--font-mono); font-size: 11px; }
.hero-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 12px; }
.hero-card {
  padding: 14px; background: var(--bg-slate); border: 1px solid var(--line); border-radius: 8px;
}
.hero-card .t { font-size: 11px; color: var(--text-dim); }
.hero-card .n { font-size: 26px; color: var(--amber); font-family: var(--font-mono); }
input:focus, select:focus, textarea:focus {
  outline: 1px solid var(--amber); outline-offset: 1px;
}
"""

DASH = r"""
export const dashboardViewTemplate = `
<section class="panel">
  <h2>闸口总览</h2>
  <p class="hint">过磅票入闸后裁定超重才放行，驳回进旁路挂起；闸代快照须与提单册对账。</p>
  <div class="hero-cards">
    <div class="hero-card"><span class="t">地磅桥</span><div class="n">{{ dash.bridges ?? '—' }}</div></div>
    <div class="hero-card"><span class="t">开放超重</span><div class="n">{{ dash.open_overloads ?? '—' }}</div></div>
    <div class="hero-card"><span class="t">旁路挂起</span><div class="n">{{ dash.side_pending ?? '—' }}</div></div>
    <div class="hero-card"><span class="t">过磅票</span><div class="n">{{ dash.tickets ?? '—' }}</div></div>
    <div class="hero-card"><span class="t">已放行</span><div class="n">{{ dash.gate_releases ?? '—' }}</div></div>
    <div class="hero-card"><span class="t">已封闸</span><div class="n">{{ dash.gate_seals ?? '—' }}</div></div>
  </div>
  <p class="hint" style="margin-top:16px">骨架：{{ dash.meta && dash.meta.skeleton }}</p>
</section>
`;"""

BRIDGES = r"""
export const bridgesViewTemplate = `
<section class="panel">
  <h2>地磅桥登记</h2>
  <p class="hint">登记港区地磅额定毛重与轴数上限，供车道阈值引用。</p>
  <div class="form-row">
    <div><label>地磅编码</label><input v-model="bridgeForm.bridge_code"/></div>
    <div><label>港区</label><input v-model="bridgeForm.pier_zone"/></div>
    <div><label>名称</label><input v-model="bridgeForm.name"/></div>
    <div><label>额定毛重(吨)</label><input v-model.number="bridgeForm.max_gross_t" type="number"/></div>
    <div><label>轴数上限</label><input v-model.number="bridgeForm.axle_limit" type="number"/></div>
  </div>
  <div class="actions">
    <button @click="createBridge">登记地磅</button>
    <button class="secondary" @click="refresh">刷新</button>
  </div>
  <table class="data-table">
    <thead><tr><th>编码</th><th>港区</th><th>名称</th><th>额定量程</th><th>轴限</th><th>状态</th><th></th></tr></thead>
    <tbody>
      <tr v-for="b in bridges" :key="b.id">
        <td>{{ b.bridge_code }}</td>
        <td>{{ b.pier_zone }}</td>
        <td>{{ b.name }}</td>
        <td>{{ b.max_gross_t }}t</td>
        <td>{{ b.axle_limit }}</td>
        <td><span class="badge" :class="b.status==='运行'?'pass':'warn'">{{ b.status }}</span></td>
        <td><button class="mini-btn" @click="loadBridgeDetail(b.id)">车道</button></td>
      </tr>
    </tbody>
  </table>
  <div v-if="bridgeDetail" class="detail-box">
    <h3>{{ bridgeDetail.bridge.name }} · {{ bridgeDetail.bridge.bridge_code }}</h3>
    <p>在港票 {{ bridgeDetail.active_tickets }} · 车道 {{ bridgeDetail.lanes.length }} 条</p>
  </div>
</section>
`;"""

TICKETS = r"""
export const ticketsViewTemplate = `
<section class="panel">
  <h2>过磅票采集</h2>
  <p class="hint">录入各轴重 JSON；超重自动旁路挂起并开超重记录。</p>
  <div class="form-row">
    <div><label>车道</label>
      <select v-model.number="ticketForm.lane_id">
        <option v-for="l in lanes" :key="l.id" :value="l.id">{{ l.lane_code }}</option>
      </select>
    </div>
    <div><label>提单号</label>
      <select v-model="ticketForm.bl_ref">
        <option v-for="b in blList" :key="b.bl_code" :value="b.bl_code">{{ b.bl_code }}</option>
      </select>
    </div>
    <div><label>车牌</label><input v-model="ticketForm.vehicle_plate"/></div>
    <div><label>票号(可空)</label><input v-model="ticketForm.ticket_code"/></div>
  </div>
  <label>轴重 JSON</label>
  <textarea v-model="ticketForm.axles_json" rows="4" placeholder='[{"axle":1,"w":8.2}]'></textarea>
  <div class="actions">
    <button @click="createTicket">过磅入闸</button>
    <button class="secondary" @click="refresh">刷新</button>
  </div>
  <table class="data-table">
    <thead><tr><th>票号</th><th>车道</th><th>提单</th><th>毛重</th><th>状态</th><th>代</th><th></th></tr></thead>
    <tbody>
      <tr v-for="t in tickets" :key="t.id" @click="selectTicket(t)">
        <td>{{ t.ticket_code }}</td>
        <td>{{ t.lane_code }}</td>
        <td>{{ t.bl_ref }}</td>
        <td>{{ fmtT(t.gross_t) }}</td>
        <td><span class="badge" :class="ticketClass(t.status)">{{ t.status }}</span></td>
        <td>{{ t.generation }}</td>
        <td><button class="mini-btn" @click.stop="loadTicketDetail(t.id)">详情</button></td>
      </tr>
    </tbody>
  </table>
  <div v-if="ticketDetail" class="detail-box">
    <p>车牌 {{ ticketDetail.ticket.vehicle_plate }} · 超重挂起 {{ ticketDetail.overload_holds.length }} 条</p>
  </div>
</section>
`;"""

OVERLOAD = r"""
export const overloadViewTemplate = `
<section class="panel">
  <h2>超重旁路</h2>
  <p class="hint">开放挂起驶向旁路；闭环后票态回到已裁定方可放行。</p>
  <div class="form-row">
    <div><label>过磅票</label>
      <select v-model.number="overloadOpenForm.ticket_id">
        <option v-for="t in adjudicableTickets" :key="t.id" :value="t.id">{{ t.ticket_code }}</option>
      </select>
    </div>
    <div><label>旁路备注</label><input v-model="overloadOpenForm.side_lane_note"/></div>
  </div>
  <div class="actions">
    <button @click="openOverload">人工挂起</button>
    <button class="secondary" @click="refresh">刷新</button>
  </div>
  <table class="data-table">
    <thead><tr><th>键</th><th>票号</th><th>超重</th><th>阈值</th><th>状态</th><th></th></tr></thead>
    <tbody>
      <tr v-for="h in overloads" :key="h.id">
        <td class="mono">{{ h.hold_key }}</td>
        <td>{{ h.ticket_code }}</td>
        <td>{{ h.overweight_t }}t</td>
        <td>{{ h.threshold_t }}t</td>
        <td><span class="badge" :class="h.status==='开放'?'fail':'pass'">{{ h.status }}</span></td>
        <td>
          <button v-if="h.status==='开放'" class="mini-btn" @click="closeOverload(h.id)">闭环</button>
        </td>
      </tr>
    </tbody>
  </table>
</section>
`;"""

GATE = r"""
export const gateViewTemplate = `
<section class="panel">
  <h2>闸口放行</h2>
  <p class="hint">须票态已裁定且无开放超重挂起；旁路未闭环不得抬杆。</p>
  <div class="form-row">
    <div><label>过磅票</label>
      <select v-model.number="gateForm.ticket_id">
        <option v-for="t in releasableTickets" :key="t.id" :value="t.id">{{ t.ticket_code }}</option>
      </select>
    </div>
    <div><label>值班员</label><input v-model="gateForm.officer"/></div>
  </div>
  <div class="actions">
    <button @click="releaseGate">确认放行</button>
    <button class="secondary" @click="refresh">刷新</button>
  </div>
  <table class="data-table">
    <thead><tr><th>放行号</th><th>票号</th><th>车道</th><th>值班员</th><th>时间</th></tr></thead>
    <tbody>
      <tr v-for="g in gateReleases" :key="g.id">
        <td>{{ g.release_ref }}</td>
        <td>{{ g.ticket_code }}</td>
        <td>{{ g.lane_code }}</td>
        <td>{{ g.officer }}</td>
        <td>{{ g.released_at }}</td>
      </tr>
    </tbody>
  </table>
</section>
`;"""

SEAL = r"""
export const sealViewTemplate = `
<section class="panel">
  <h2>闸代快照</h2>
  <p class="hint">封闸升代并写入清单摘要，供提单册对账引用。</p>
  <div class="form-row">
    <div><label>过磅票</label>
      <select v-model.number="sealForm.ticket_id">
        <option v-for="t in sealableTickets" :key="t.id" :value="t.id">{{ t.ticket_code }}</option>
      </select>
    </div>
    <div><label>清单(可空)</label><input v-model="sealForm.manifest"/></div>
  </div>
  <div class="actions">
    <button @click="createSeal">写入快照</button>
    <button class="secondary" @click="refresh">刷新</button>
  </div>
  <table class="data-table">
    <thead><tr><th>快照号</th><th>票号</th><th>闸代</th><th>清单摘要</th><th>状态</th></tr></thead>
    <tbody>
      <tr v-for="s in seals" :key="s.id">
        <td>{{ s.seal_ref }}</td>
        <td>{{ s.ticket_code }}</td>
        <td>{{ s.ticket_generation }}</td>
        <td class="mono">{{ shortText(s.manifest) }}</td>
        <td><span class="badge pass">{{ s.status }}</span></td>
      </tr>
    </tbody>
  </table>
</section>
`;"""

BL = r"""
export const blViewTemplate = `
<section class="panel">
  <h2>提单册</h2>
  <p class="hint">到港提单须先登记，过磅票引用提单号。</p>
  <div class="form-row">
    <div><label>提单号</label><input v-model="blForm.bl_code"/></div>
    <div><label>货描</label><input v-model="blForm.cargo_desc"/></div>
    <div><label>申报毛重(吨)</label><input v-model.number="blForm.declared_gross_t" type="number"/></div>
    <div><label>船名航次</label><input v-model="blForm.vessel_voyage"/></div>
  </div>
  <div class="actions">
    <button @click="registerBl">登记提单</button>
    <button class="secondary" @click="refresh">刷新</button>
  </div>
  <table class="data-table">
    <thead><tr><th>提单</th><th>货描</th><th>申报吨</th><th>航次</th><th>状态</th></tr></thead>
    <tbody>
      <tr v-for="b in blList" :key="b.id">
        <td>{{ b.bl_code }}</td>
        <td>{{ b.cargo_desc }}</td>
        <td>{{ b.declared_gross_t }}</td>
        <td>{{ b.vessel_voyage }}</td>
        <td>{{ b.status }}</td>
      </tr>
    </tbody>
  </table>
</section>
`;"""

LINEAGE = r"""
export const lineageViewTemplate = `
<section class="panel">
  <h2>轴重血缘</h2>
  <p class="hint">记录驳载分票、二次过磅等轴重血缘边。</p>
  <div class="form-row">
    <div><label>起点票</label>
      <select v-model.number="lineageForm.from_ticket_id">
        <option v-for="t in tickets" :key="t.id" :value="t.id">{{ t.ticket_code }}</option>
      </select>
    </div>
    <div><label>终点票(可空)</label>
      <select v-model.number="lineageForm.to_ticket_id">
        <option :value="null">—</option>
        <option v-for="t in tickets" :key="t.id" :value="t.id">{{ t.ticket_code }}</option>
      </select>
    </div>
    <div><label>类型</label><input v-model="lineageForm.edge_type"/></div>
    <div><label>说明</label><input v-model="lineageForm.detail"/></div>
  </div>
  <div class="actions">
    <button @click="addLineage">登记边</button>
    <button class="secondary" @click="refresh">刷新</button>
  </div>
  <table class="data-table">
    <thead><tr><th>自</th><th>至</th><th>类型</th><th>说明</th></tr></thead>
    <tbody>
      <tr v-for="e in lineageEdges" :key="e.id">
        <td>{{ e.from_code || e.from_ticket_id }}</td>
        <td>{{ e.to_code || '—' }}</td>
        <td>{{ e.edge_type }}</td>
        <td>{{ e.detail }}</td>
      </tr>
    </tbody>
  </table>
</section>
`;"""

RECON = r"""
export const reconcileViewTemplate = `
<section class="grid-2">
  <section class="panel">
    <h2>提单对账</h2>
    <p class="hint">汇总过磅毛重与提单申报吨比对。</p>
    <div class="form-row">
      <div><label>提单号</label><input v-model="reconCode"/></div>
    </div>
    <div class="actions">
      <button @click="loadReconcile">对账</button>
      <button class="secondary" @click="loadAllReconcile">全量</button>
    </div>
    <div v-if="reconOne" class="detail-box">
      <p>申报 {{ reconOne.declared_gross_t }}t · 过磅合计 {{ reconOne.ticket_sum_t }}t</p>
      <p :class="reconOne.balanced ? 'ok' : 'bad'">{{ reconOne.balanced ? '账实平衡' : '偏差待查' }}</p>
      <p>快照数 {{ reconOne.seal_count }} · 可出证明 {{ reconOne.proof_ready ? '是' : '否' }}</p>
    </div>
    <ul v-if="reconAllItems.length">
      <li v-for="r in reconAllItems" :key="r.bl_code">{{ r.bl_code }} · {{ r.balanced ? '平' : '偏' }}</li>
    </ul>
  </section>
  <section class="panel">
    <h2>单票证明</h2>
    <div class="form-row"><div><label>票号</label><input v-model="proofCode"/></div></div>
    <motion class="actions"><button @click="loadProof">拉证明</button></motion>
    <div v-if="proofOne" class="detail-box">
      <p>提单匹配 {{ proofOne.manifest_matches_bl ? '是' : '否' }}</p>
      <p>超重闭环 {{ proofOne.overload_closed ? '是' : '否' }}</p>
      <p>已放行 {{ proofOne.released ? '是' : '否' }}</p>
      <p>一致 {{ proofOne.coherent ? '是' : '否' }}</p>
    </div>
  </section>
</section>
`;"""

STUBS = r"""
export const stubsViewTemplate = `
<section class="grid-2">
  <section class="panel">
    <h2>海关申报空桩</h2>
    <p class="hint">接口已挂载，回执未对接。</p>
    <div class="form-row">
      <div><label>提单</label><input v-model="customsForm.bl_code"/></div>
      <div><label>行数</label><input v-model.number="customsForm.row_count" type="number"/></div>
    </div>
    <div class="actions"><button @click="enqueueCustoms">入队</button></div>
    <table class="data-table compact">
      <tr v-for="j in customsJobs" :key="j.id"><td>{{ j.bl_code }}</td><td>{{ j.status }}</td></tr>
    </table>
  </section>
  <section class="panel">
    <h2>岸桥计划空桩</h2>
    <div class="form-row">
      <div><label>泊位</label><input v-model="craneForm.berth_slot"/></div>
      <div><label>票ID(可空)</label><input v-model.number="craneForm.ticket_id" type="number"/></div>
    </div>
    <div class="actions"><button @click="enqueueCrane">入队</button></div>
    <table class="data-table compact">
      <tr v-for="j in craneJobs" :key="j.id"><td>{{ j.berth_slot }}</td><td>{{ j.status }}</td></tr>
    </table>
  </section>
</section>
`;"""

API_JS = r"""
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
"""

APP_JS = r"""
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
        await api.closeOverload({ hold_id: holdId, note: "前端闭环" });
        flashOk("挂起已闭"); await refresh();
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

    const viewMap = [
      dashboardViewTemplate, bridgesViewTemplate, lanesViewTemplate, ticketsViewTemplate,
      overloadViewTemplate, gateViewTemplate, sealViewTemplate, blViewTemplate,
      lineageViewTemplate, reconcileViewTemplate, stubsViewTemplate,
    ];

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
      adjudicableTickets, releasableTickets, sealableTickets,
      login, logout, refresh, viewMap,
      fmtT, ticketClass, shortText,
      createBridge, loadBridgeDetail, createLane, createTicket, loadTicketDetail, selectTicket,
      openOverload, closeOverload, releaseGate, createSeal, registerBl, addLineage,
      loadReconcile, loadAllReconcile, loadProof, enqueueCustoms, enqueueCrane,
    };
  },
  template: `
    <motion v-if="!token" class="login-hero">
      <UploadLogin class="login-card">
        <h1>港口过磅闸口</h1>
        <p class="sub">过磅票入闸后裁定超重才放行，驳回进旁路挂起，闸代快照与提单册对账。</p>
        <label>账号</label><input v-model="username"/>
        <label>密码</label><input v-model="password" type="password"/>
        <button @click="login">登录</button>
        <p v-if="err" class="err">{{ err }}</p>
      </UploadLogin>
    </motion>
    <motion v-else class="harbor-shell">
      <header class="harbor-top">
        <motion style="display:flex;flex-wrap:wrap;align-items:flex-start;gap:16px;width:100%">
          <motion>
            <h1>港口过磅闸口</h1>
            <p class="tagline">数据工程 · 港区地磅闸口裁定</p>
          </motion>
          <motion class="stat-strip">
            <span class="stat-pill">超重<strong>{{ dash.open_overloads ?? 0 }}</strong></span>
            <span class="stat-pill">旁路<strong>{{ dash.side_pending ?? 0 }}</strong></span>
            <span class="stat-pill">在港票<strong>{{ dash.tickets ?? 0 }}</strong></span>
          </motion>
          <motion class="top-actions">
            <span>{{ user }}</span>
            <button @click="refresh">刷新</button>
            <button @click="logout">退出</button>
          </motion>
        </motion>
      </header>
      <nav class="tab-strip">
        <button v-for="(n,i) in nav" :key="n" :class="{active: tab===i}" @click="tab=i">{{ n }}</button>
      </nav>
      <main class="harbor-main">
        <p v-if="actionErr" class="action-err">{{ actionErr }}</p>
        <p v-if="actionOk" class="ok-msg">{{ actionOk }}</p>
        <component :is="{ template: viewMap[tab] }" />
      </main>
    </motion>
  `,
}).mount("#app");
"""

# Fix typos in APP_JS template - motion/UploadLogin should be div
APP_JS = APP_JS.replace("<motion", "<div").replace("</motion>", "</div>").replace("UploadLogin", "div")

LANES = r"""
export const lanesViewTemplate = `
<section class="panel">
  <h2>过磅车道</h2>
  <p class="hint">每车道配置超限阈值与旁路引用；进闸方向与出闸方向分开编码。</p>
  <div class="form-row">
    <div><label>车道编码</label><input v-model="laneForm.lane_code"/></div>
    <div><label>所属地磅</label>
      <select v-model.number="laneForm.bridge_id">
        <option v-for="b in bridges" :key="b.id" :value="b.id">{{ b.bridge_code }}</option>
      </select>
    </div>
    <div><label>方向</label><input v-model="laneForm.direction" placeholder="进闸/出闸"/></div>
    <div><label>超限阈值(吨)</label><input v-model.number="laneForm.overload_threshold_t" type="number"/></div>
    <div><label>旁路</label><input v-model="laneForm.side_lane_ref"/></div>
  </div>
  <div class="actions">
    <button @click="createLane">开通车道</button>
    <button class="secondary" @click="refresh">刷新</button>
  </div>
  <table class="data-table">
    <thead><tr><th>车道</th><th>地磅</th><th>方向</th><th>阈值</th><th>旁路</th><th>状态</th></tr></thead>
    <tbody>
      <tr v-for="l in lanes" :key="l.id">
        <td>{{ l.lane_code }}</td>
        <td>{{ l.bridge_code }}</td>
        <td>{{ l.direction }}</td>
        <td>{{ l.overload_threshold_t }}t</td>
        <td>{{ l.side_lane_ref || '—' }}</td>
        <td><span class="badge pass">{{ l.status }}</span></td>
      </tr>
    </tbody>
  </table>
</section>
`;"""

RECON = RECON.replace("<motion class", "<div class").replace("</motion>", "</div>")


if __name__ == "__main__":
    main()