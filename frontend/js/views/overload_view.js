export const overloadViewTemplate = `
<!-- 第30号·回态修辰：驳回按钮接 /api/overloads/reject 同一甲路径；成败都以主票状态列回态为准 -->
<section class="panel">
  <h2>超重旁路</h2>
  <p class="hint">开放挂起驶向旁路；驳回写口同事务把主票状态列回写为已裁定并抹掉旁路位，放行页/对账/总览随之同源回正。</p>
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
    <thead><tr><th>键</th><th>票号</th><th>超重</th><th>阈值</th><th>挂起状态</th><th>主票状态列</th><th></th></tr></thead>
    <tbody>
      <tr v-for="h in overloads" :key="h.id">
        <td class="mono">{{ h.hold_key }}</td>
        <td>{{ h.ticket_code }}</td>
        <td>{{ h.overweight_t }}t</td>
        <td>{{ h.threshold_t }}t</td>
        <td><span class="badge" :class="h.status==='开放'?'fail':'pass'">{{ h.status }}</span></td>
        <td><span class="badge" :class="ticketClass(h.ticket_status)">{{ h.ticket_status || '—' }}</span></td>
        <td>
          <button v-if="h.status==='开放'" class="mini-btn" @click="closeOverload(h.id)">驳回回态</button>
        </td>
      </tr>
    </tbody>
  </table>
</section>
`;
