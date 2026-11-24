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
`;