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
`;