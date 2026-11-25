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
    <button @click="releaseGate" :disabled="!gateForm.ticket_id">确认放行</button>
    <button class="secondary" @click="refresh">刷新</button>
  </div>
  <!-- 第30号：按钮灰掉的同源解释：这些票主票状态列仍是旁路挂起，须先超重页驳回回态 -->
  <div v-if="bypassBlockedTickets.length" class="detail-box" style="border-color:#c0392b">
    <p class="bad" style="font-weight:600">以下 {{ bypassBlockedTickets.length }} 张票仍旁路挂起，放行按钮对其不可选：</p>
    <p v-for="t in bypassBlockedTickets" :key="t.id" class="bad mono">
      · {{ t.ticket_code }}（{{ t.status }}）— 请先在「超重」页点“驳回回态”
    </p>
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
`;