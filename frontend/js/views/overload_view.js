export const overloadViewTemplate = `
<!-- BUGFIX-15 埋雷：驳回闭环不提示票态回写 -->

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
`;