export const dashboardViewTemplate = `
<!-- 第30号·回态修辰：总览与超重/过磅/放行/对账五页同源 weigh_tickets.status -->
<section class="panel">
  <h2>闸口总览</h2>
  <p class="hint">过磅票入闸后裁定超重才放行，驳回进旁路挂起；驳回写口同事务回写票态为已裁定并抹掉旁路位后，五页计数一起回正。</p>
  <div class="hero-cards">
    <div class="hero-card"><span class="t">地磅桥</span><div class="n">{{ dash.bridges ?? '—' }}</div></div>
    <div class="hero-card"><span class="t">开放超重</span><div class="n">{{ dash.open_overloads ?? '—' }}</div></div>
    <div class="hero-card" :class="dash.side_pending ? 'card-fail' : 'card-pass'">
      <span class="t">旁路挂起（未回态）</span><div class="n">{{ dash.side_pending ?? '—' }}</div>
    </div>
    <div class="hero-card card-pass"><span class="t">已裁定（驳回已回态）</span><div class="n">{{ dash.adjudicated ?? '—' }}</div></div>
    <div class="hero-card"><span class="t">过磅票</span><div class="n">{{ dash.tickets ?? '—' }}</div></div>
    <div class="hero-card"><span class="t">已放行</span><div class="n">{{ dash.gate_releases ?? '—' }}</div></div>
    <div class="hero-card"><span class="t">已封闸</span><div class="n">{{ dash.gate_seals ?? '—' }}</div></div>
  </div>

  <div class="detail-box" style="margin-top:16px">
    <p class="t" style="font-weight:600">五页同源票态核对</p>
    <p v-if="!dash.side_pending" class="ok">无旁路挂起票：驳回均已回态，放行页可选、对账卡为已裁定，不存在“闭挂起却仍旁路/可重裁”的分叉。</p>
    <div v-else>
      <p class="bad">仍有 {{ dash.side_pending }} 张票主票状态列停留在旁路挂起，须在超重页驳回回态：</p>
      <p class="mono bad" v-for="code in (dash.side_pending_codes || [])" :key="code">· {{ code }}</p>
    </div>
  </div>

  <p class="hint" style="margin-top:16px">骨架：{{ dash.meta?.skeleton }}</p>
</section>
`;
