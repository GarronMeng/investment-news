(()=>{
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const n=v=>Number.isFinite(Number(v))?Number(v):null;
  const pct=v=>n(v)==null?'—':`${n(v)>0?'+':''}${n(v).toFixed(1)}%`;
  const tone=v=>n(v)==null?'neutral':n(v)>0?'up':n(v)<0?'down':'neutral';
  const signalLabel={strong_growth:'高增长',positive_growth:'正增长',mixed:'分化',weak_growth:'承压',unknown:'数据不足',not_reported:'待披露'};
  const breadthLabel={positive:'已披露偏强',mixed:'已披露分化',weak:'已披露偏弱',awaiting_reports:'等待披露'};
  const style=document.createElement('style');
  style.textContent='.macro-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.macro-event{display:grid;grid-template-columns:68px 1fr;gap:9px;border:1px solid var(--line);border-radius:9px;background:var(--paper);padding:9px}.macro-meta{font-size:10px;color:var(--muted);margin-top:3px}.macro-chip{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:1px 6px;margin:2px 3px 0 0;font-size:9px;color:var(--muted)}.earn-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.earn-theme{border:1px solid var(--line);border-radius:10px;background:var(--paper);padding:10px}.earn-head{display:flex;justify-content:space-between;gap:8px}.earn-list{margin-top:7px}.earn-row{display:grid;grid-template-columns:minmax(85px,1.2fr) .8fr .9fr .9fr;gap:6px;padding:6px 0;border-top:1px dashed var(--line);align-items:center}.earn-row:first-child{border-top:0}.earn-row span{font-size:10px}.earn-summary{display:flex;gap:6px;flex-wrap:wrap;margin-top:5px}.earn-summary .tag{background:var(--soft)}@media(max-width:800px){.macro-grid,.earn-grid{grid-template-columns:1fr}.earn-row{grid-template-columns:1.2fr .8fr .8fr}.earn-row .profit{display:none}}';
  document.head.appendChild(style);

  function sectionByTitle(text){return [...document.querySelectorAll('.section')].find(el=>el.querySelector('.section-title')?.textContent.includes(text));}
  function bjDate(offset=0){const now=new Date(Date.now()+offset*86400000);return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);}
  function addDays(iso,days){const d=new Date(`${iso}T00:00:00+08:00`);d.setUTCDate(d.getUTCDate()+days);return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(d);}
  function renderBeijingCalendar(rows){
    const root=document.getElementById('calendar'); if(!root)return;
    const today=bjDate(), tomorrow=addDays(today,1), d10=addDays(today,10);
    const groups=[
      ['今天',r=>r.date===today],
      ['明天',r=>r.date===tomorrow],
      ['未来10天',r=>r.date>tomorrow&&r.date<=d10],
    ];
    root.innerHTML=groups.map(([title,fn])=>{const items=(rows||[]).filter(fn);return `<div class="calendar-group"><h3>${esc(title)}</h3>${items.length?items.map(r=>`<div class="cal-row"><div class="cal-date">${esc((r.date||'').slice(5,10))}</div><div><b>${esc(r.title||'—')}</b><div class="micro">${esc(r.importance||'—')} · ${esc(r.status||'—')}${(r.assets||[]).length?` · 关联 ${esc(r.assets.join(' / '))}`:''}</div></div></div>`).join(''):'<div class="empty">暂无已接入事件</div>'}</div>`}).join('');
  }
  function macroSection(events,summary){
    const section=document.createElement('section'); section.className='section';
    const rows=(events||[]).slice(0,16);
    const body=rows.length?`<div class="macro-grid">${rows.map(e=>`<div class="macro-event"><div class="datepill">${esc((e.date||'—').slice(5,10))}<br>${esc(e.time||'')}</div><div><b>${esc(e.region||e.type||'')} · ${esc(e.title||'—')}</b><div class="macro-meta">${esc(e.type==='global_earnings'?`财报期 ${e.report_period||'—'}`:`预期 ${e.forecast??'—'} · 前值 ${e.previous??'—'}`)} · 重要性 ${esc(e.importance??'—')}</div><div>${(e.impact_channels||[]).map(x=>`<span class="macro-chip">${esc(x)}</span>`).join('')}${(e.themes||[]).map(x=>`<span class="macro-chip">${esc(x)}</span>`).join('')}</div></div></div>`).join('')}</div>`:'<div class="panel empty">未来10天暂无已接入的高重要性宏观/海外财报事件，或数据源待恢复。</div>';
    section.innerHTML=`<h2 class="section-title">宏观与海外催化 · 未来10天</h2><div class="micro" style="margin:-5px 0 8px">宏观 ${esc(summary?.macro??0)} 条 · 海外核心公司财报 ${esc(summary?.global_earnings??0)} 条 · 缺失不补造日期</div>${body}`;
    return section;
  }

  function earningsSection(themes,period,summary){
    const section=document.createElement('section'); section.className='section';
    const rows=(themes||[]);
    const body=rows.length?`<div class="earn-grid">${rows.map(t=>{const s=t.summary||{};return `<div class="earn-theme"><div class="earn-head"><div><b>${esc(t.theme||'—')}</b><div class="micro">${esc(period||'当前报告期')} · ${esc(breadthLabel[s.breadth]||s.breadth||'—')}</div></div><span class="tag">${esc(s.reported??0)}/${esc(s.total??0)} 已披露</span></div><div class="earn-summary"><span class="tag">营收YoY中位 ${pct(s.median_revenue_yoy_pct)}</span><span class="tag">净利YoY中位 ${pct(s.median_net_profit_yoy_pct)}</span><span class="tag">待披露 ${esc((s.scheduled??0)+(s.pending??0))}</span></div><div class="earn-list">${(t.companies||[]).slice(0,6).map(c=>`<div class="earn-row"><span><b>${esc(c.name||c.code)}</b><br><span class="micro">${esc(c.status==='reported'?(c.announcement_date||'已披露'):(c.scheduled_date||'待定'))}</span></span><span class="${tone(c.revenue_yoy_pct)}">营收 ${pct(c.revenue_yoy_pct)}</span><span class="profit ${tone(c.net_profit_yoy_pct)}">净利 ${pct(c.net_profit_yoy_pct)}</span><span>${esc(signalLabel[c.earnings_signal]||c.earnings_signal||'—')}</span></div>`).join('')}</div></div>`}).join('')}</div>`:'<div class="panel empty">主题财报跟踪数据待接入。</div>';
    section.innerHTML=`<h2 class="section-title">主线财报跟踪</h2><div class="micro" style="margin:-5px 0 8px">代表性研究样本 ${esc(summary?.reported??0)}/${esc(summary?.companies??0)} 已披露；只描述已披露样本，不外推全行业。</div>${body}`;
    return section;
  }

  Promise.all([
    fetch('daily_flash.json',{cache:'no-store'}).then(r=>r.json()).catch(()=>({})),
    fetch('macro_calendar.json',{cache:'no-store'}).then(r=>r.json()).catch(()=>({})),
    fetch('theme_earnings.json',{cache:'no-store'}).then(r=>r.json()).catch(()=>({}))
  ]).then(([D,M,T])=>{
    renderBeijingCalendar(D.catalysts||[]);
    const macroEvents=D.macro_calendar||M.events||[];
    const macroSummary=D.macro_calendar_summary||M.summary||{};
    const themeRows=D.theme_earnings||T.themes||[];
    const themeSummary=D.theme_earnings_summary||T.summary||{};
    const period=D.theme_earnings_period||T.report_period;
    const macro=macroSection(macroEvents,macroSummary);
    const cal=sectionByTitle('财报 / 催化日历');
    if(cal)cal.after(macro); else document.querySelector('main')?.append(macro);
    const earnings=earningsSection(themeRows,period,themeSummary);
    const theme=sectionByTitle('主线跟踪');
    if(theme)theme.after(earnings); else macro.after(earnings);
  }).catch(console.warn);
})();
