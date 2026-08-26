(()=>{
  if(document.querySelector('meta[name="dashboard-mode"][content="decision-cockpit"]'))return;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num=(v,d=2)=>Number.isFinite(Number(v))?Number(v).toFixed(d):'—';
  const signed=(v,d=2)=>Number.isFinite(Number(v))?`${Number(v)>0?'+':''}${Number(v).toFixed(d)}`:'—';
  const tone=v=>!Number.isFinite(Number(v))?'neutral':Number(v)>0?'up':Number(v)<0?'down':'neutral';
  const style=document.createElement('style');
  style.textContent='.funding-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.funding-card{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:10px}.funding-card b{display:block;font-size:18px;margin:2px 0}.futures-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin-top:9px}.future{background:var(--soft);border-radius:8px;padding:8px}.future strong{display:block;font-size:13px}@media(max-width:900px){.funding-grid,.futures-grid{grid-template-columns:repeat(2,1fr)}}';
  document.head.appendChild(style);

  function card(title,value,sub,klass='neutral'){
    return `<div class="funding-card"><div class="kicker">${esc(title)}</div><b class="${klass}">${esc(value)}</b><div class="micro">${esc(sub)}</div></div>`;
  }
  function render(D){
    const x=D.market?.funding_and_futures;
    if(!x)return;
    const m=x.margin||{},s=x.southbound||{},f=x.index_futures||[];
    const section=document.createElement('section');section.className='section';
    const marginVal=m.financing_balance_cny_100m==null?'—':`${num(m.financing_balance_cny_100m,0)}亿`;
    const marginChange=m.change_5d_pct==null?'5日变化待更新':`5日 ${signed(m.change_5d_pct)}%`;
    const southVal=s.net_buy_cny_100m==null?'—':`${signed(s.net_buy_cny_100m,1)}亿`;
    const southSub=`南向成交净买额 · ${s.as_of||'—'} · ${s.status||'—'}`;
    const fFresh=f.filter(r=>r.status==='fresh');
    const avgBasis=fFresh.map(r=>Number(r.basis_pct)).filter(Number.isFinite);
    const mean=avgBasis.length?avgBasis.reduce((a,b)=>a+b,0)/avgBasis.length:null;
    section.innerHTML=`<h2 class="section-title">资金与股指期货</h2><div class="funding-grid">${card('融资余额',marginVal,`${marginChange} · ${m.as_of||'—'} · ${m.status||'—'}`,tone(m.change_5d_pct))}${card('融资买入额',m.financing_buy_cny_100m==null?'—':`${num(m.financing_buy_cny_100m,0)}亿`,'两融情绪公开汇总',tone(m.change_1d_pct))}${card('南向资金',southVal,southSub,tone(s.net_buy_cny_100m))}${card('股指期货平均基差',mean==null?'—':`${signed(mean,2)}%`,fFresh.length?`${fFresh.length} 个已映射主力合约`:'CFFEX数据待恢复',tone(mean))}</div><div class="futures-grid">${f.length?f.map(r=>`<div class="future"><div class="kicker">${esc(r.underlying||r.symbol||'股指期货')}</div><strong class="${tone(r.basis_pct)}">基差 ${r.basis_pct==null?'—':`${signed(r.basis_pct,2)}%`}</strong><div class="micro">期货 ${num(r.current_price,1)} · 现货 ${num(r.spot,1)} · ${esc(r.status||'—')}</div></div>`).join(''):'<div class="empty">股指期货数据待接入/恢复</div>'}</div>`;
    const sections=[...document.querySelectorAll('.section')];
    const anchor=sections.find(el=>el.querySelector('.section-title')?.textContent.includes('指数与盘面总览'));
    if(anchor)anchor.after(section);else document.querySelector('main')?.prepend(section);
  }
  fetch('daily_flash.json',{cache:'no-store'}).then(r=>r.json()).then(render).catch(console.warn);
})();
