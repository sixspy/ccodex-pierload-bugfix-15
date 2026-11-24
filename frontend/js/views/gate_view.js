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
`;