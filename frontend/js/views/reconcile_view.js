export const reconcileViewTemplate = `
<!-- 第30号·回态修辰：对账页裁定卡片只认正式票态列，点破“影子未晋升却写可重裁”的双口径 -->
<section class="grid-2">
  <section class="panel">
    <h2>提单对账</h2>
    <p class="hint">汇总过磅毛重与提单申报吨比对；裁定状态与超重/过磅/放行/总览五页同源，只认正式票态列，不认影子回态草稿。</p>
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

      <div class="adjudication-card" :class="reconOne.all_adjudicated ? 'pass' : 'fail'">
        <span class="t">对账裁定卡 · 正式票态同源</span>
        <div class="adj-label">
          <span class="badge" :class="reconOne.all_adjudicated ? 'pass' : 'fail'">
            {{ reconOne.adjudication_label || '—' }}
          </span>
        </div>
        <p v-if="reconOne.all_adjudicated" class="ok">
          驳回已同事务回态：票态为已裁定（含已放行/已封闸），可放行、可出账，不存在“可重裁”挂起。
        </p>
        <p v-else class="bad">
          仍有旁路挂起
          {{ (reconOne.adjudication?.side_pending) || 0 }}
          票未回态：对账不得写成“可重裁/已裁定”；影子回态未原子晋升前一律不作数。
        </p>
        <table v-if="reconOne.tickets?.length" class="data-table">
          <thead><tr><th>票号</th><th>主票状态列</th><th>旁路位</th><th>毛重</th></tr></thead>
          <tbody>
            <tr v-for="t in reconOne.tickets" :key="t.ticket_code">
              <td class="mono">{{ t.ticket_code }}</td>
              <td><span class="badge" :class="ticketClass(t.status)">{{ t.status }}</span></td>
              <td>{{ t.bypass_pending ? '挂起中' : '已抹除' }}</td>
              <td>{{ t.gross_t }}t</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <ul v-if="reconAllItems.length">
      <li v-for="r in reconAllItems" :key="r.bl_code">
        {{ r.bl_code }} · {{ r.balanced ? '平' : '偏' }} ·
        <span :class="r.all_adjudicated ? 'ok' : 'bad'">{{ r.adjudication_label || '票态未知' }}</span>
      </li>
    </ul>
  </section>
  <section class="panel">
    <h2>单票证明</h2>
    <div class="form-row"><div><label>票号</label><input v-model="proofCode"/></div></div>
    <div class="actions"><button @click="loadProof">拉证明</button></div>
    <div v-if="proofOne" class="detail-box">
      <p>主票状态 <span class="badge" :class="ticketClass(proofOne.ticket_status)">{{ proofOne.ticket_status || '—' }}</span></p>
      <p :class="proofOne.bypass_pending ? 'bad' : 'ok'">
        旁路位 {{ proofOne.bypass_pending ? '仍在（驳回未回态）' : '已抹除' }}
      </p>
      <p>提单匹配 {{ proofOne.manifest_matches_bl ? '是' : '否' }}</p>
      <p>超重闭环 {{ proofOne.overload_closed ? '是' : '否' }}</p>
      <p>已放行 {{ proofOne.released ? '是' : '否' }}</p>
      <p>一致 {{ proofOne.coherent ? '是' : '否' }}</p>
    </div>
  </section>
</section>
`;
