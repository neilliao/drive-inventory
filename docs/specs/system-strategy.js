(() => {
const all=window.systemStrategyData;
const d=all.find(x=>location.pathname.endsWith(x.file)); if(!d)return;
const tier=window.systemTierData.find(x=>x.key===d.key);
const old=document.querySelector('.wrap');
const main=document.createElement('main'); main.className='system-blueprint';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dependencies={registry:'先確認一份人的正本，再讓名單與授權有共同依據。',library:'道籍提供人員與職務依據；個資複核後才能開放取用。',portal:'等知識庫正本與權限確認，再接入口；不另存一份資料。',media:'取用已確認的素材，採集成果回存知識庫，審核故事再進典藏。',archive:'承接知識庫素材與媒體編審成果，先內容、後展示。'};
if(d.connection)dependencies[d.key]=d.connection;
main.innerHTML=`<nav class="sb-nav"><a href="2026-08-17-strategy-map.html">← 道務文書總圖</a><a href="#sb-work">看落地工作 ↓</a></nav>
<header><p class="sb-eyebrow">細部策略 × 執行草案</p><h1>${d.title}</h1><p class="sb-goal">${d.goal}</p></header>
<figure class="sb-map"><a href="system-${d.key}-strategy.png" target="_blank" rel="noopener" aria-label="放大${d.title}策略圖"><img src="system-${d.key}-strategy.png" alt="${esc(d.chain.join('，促成'))}，達成：${d.goal}" width="1536" height="1024"></a><figcaption>點圖放大。綠箭頭是規劃中的促成關係，紅虛線是回饋；不是已驗證的因果或完成進度。</figcaption></figure>
<details class="sb-reading"><summary>小螢幕閱讀・策略關係</summary><ol>${d.chain.map(n=>`<li>${n}</li>`).join('')}</ol><p>回饋：${d.feedback}</p></details>
<aside class="sb-connection"><span>與其他系統如何相接</span><p>${dependencies[d.key]}</p><nav>${all.filter(x=>x.key!==d.key).map(x=>`<a href="${x.file}">${x.title} ↗</a>`).join('')}</nav></aside>
<section id="sb-work"><div class="sb-section-head"><div><p class="sb-eyebrow">從策略到交付</p><h2>從一個小範圍，做出可驗收的成果</h2></div><button type="button" id="sb-download">下載工作確認單 ↓</button></div>
<p class="sb-status">以下為編者整理的建議工作；現況、承辦人與日期待確認，並非已排定或已完成。</p>
<div class="sb-tasks">${d.tasks.map((t,i)=>`<details class="sb-task"><summary><span class="sb-number">${String(i+1).padStart(2,'0')}</span><span><strong>${t[0]}</strong><small>交付：${t[1]}</small></span><span class="sb-plus" aria-hidden="true">＋</span></summary><div class="sb-task-body"><dl><dt>誰來做（建議角色）</dt><dd>${t[3]}；實際人選待確認。</dd><dt>開始前</dt><dd>${i?'先確認前項交付與本項所需資料，再決定是否開始。':'確認現況、試行範圍與權責窗口。'}</dd><dt>如何驗收（建議）</dt><dd>${t[2]}</dd><dt>執行紀錄</dt><dd>承辦人、日期、成果連結及驗收人：尚未登錄。請用工作確認單記錄。</dd></dl></div></details>`).join('')}</div>
<aside class="sb-gate"><strong>開始前要守住的條件</strong><p>${d.gate}</p></aside>
<details class="sb-reading"><summary>第一次討論，只需確認這五件事</summary><ol><li>目前做到哪裡？附現況證據。</li><li>先試哪一筆資料、哪一批內容或哪一個入口？</li><li>誰承辦、誰複核？</li><li>何時交付、前置條件是否具備？</li><li>用哪份成果驗收？未通過如何修正？</li></ol></details></section>
<footer class="sb-source-note">策略、成效與驗收條件是規劃整理，不是仙佛原話。原始規劃與慈訓保留於下方；其中歷史進度未重新查核。</footer>`;
document.body.prepend(main);
const map=main.querySelector('.sb-map');
map.querySelector('img').src='system-'+d.key+'-tiered-v2.png';
map.querySelector('a').href='system-'+d.key+'-tiered-v2.png';
map.querySelector('img').alt=tier.goal+'。並行策略：'+tier.cols.map(c=>c[0]+'，預期'+c[1]+'；行動：'+c[2]).join('。')+'。支援：'+tier.supports;
map.querySelector('figcaption').textContent='由上往下看部署，由下往上看支援。各策略並行相助，不是先後步驟；箭頭與成效為規劃，非已驗證成果。';
const read=main.querySelector('.sb-reading');
read.innerHTML='<summary>閱讀策略與對應行動</summary>'+tier.cols.map(c=>'<p><strong>'+c[0]+'</strong> → '+c[1]+'<br>行動：'+c[2]+'</p>').join('')+'<p>共同支援：'+tier.supports+'</p><p>回饋：'+tier.feedback+'</p>';
const groups={registry:[[0],[1],[2]],library:[[0,1],[4],[2,3,4]],portal:[[0,2],[0,1],[1,2,3]],media:[[0,1],[2],[3]],archive:[[0,2],[1],[3]]};
if(d.groups)groups[d.key]=d.groups;
const supportForParent={registry:'存、找、傳、承：共同的人員正本、名單與職務依據。',library:'存、找、承：保存正本、提供目錄與可考據素材。',portal:'找、傳：提供入口，讓公告留底並可查找。',media:'傳、承：讓故事被理解，也留下可傳的素材。',archive:'承：將審核後的故事組織為可查找的典藏。'};
const parentNote=document.createElement('p');parentNote.className='sb-status';parentNote.textContent=d.parentText||'上承道務文書策略｜'+supportForParent[d.key];main.querySelector('header').append(parentNote);
const routes=document.createElement('nav');routes.className='sb-route-buttons';routes.setAttribute('aria-label','從策略查看落地工作');
tier.cols.forEach((c,i)=>{const b=document.createElement('button');b.type='button';b.textContent=c[0]+'・看落實 ↓';b.onclick=()=>{const tasks=[...main.querySelectorAll('.sb-task')];tasks.forEach((t,j)=>{t.open=groups[d.key][i].includes(j);});tasks[groups[d.key][i][0]].scrollIntoView({block:'start',behavior:'smooth'});tasks[groups[d.key][i][0]].querySelector('summary').focus({preventScroll:true});};routes.append(b);});map.after(routes);
if(old){const details=document.createElement('details');details.className='sb-original';details.id='source-document';const s=document.createElement('summary');s.textContent='原始規劃、慈訓與出處（深入閱讀）';details.append(s);main.after(details);details.append(old);}
const frame=document.createElement('div');frame.className='sb-image-frame';const imageLink=map.querySelector('a');imageLink.before(frame);frame.append(imageLink);
[...routes.children].forEach((b,i)=>{const hit=document.createElement('button');hit.type='button';hit.className='sb-map-hit';hit.style.left=(tier.cols.length===4?13.4+i*17.5:13+i*23.5)+'%';if(tier.cols.length===4){hit.style.width='16.5%';hit.style.height='23%';}hit.setAttribute('aria-label',b.textContent);hit.innerHTML='<span>看落實 ↗</span>';hit.onclick=b.onclick;frame.append(hit);});
if(d.key==='fahui'){
 map.querySelector('figcaption').textContent='由上往下看責任部署，由下往上看支援。圖上四條路共同服務目標；現場仍依原有抄校、核定與繳回流程，不能跳過把關。';
 const back=main.querySelector('.sb-nav a');back.href='2026-09-01-emei-wenshu-grand-strategy-map.html';back.textContent='← 峨眉文書組總圖';
 const links=main.querySelector('.sb-connection nav');links.innerHTML='<a href="2026-08-17-strategy-map.html">道務文書 ↗</a><a href="2026-08-20-knowledge-base-strategy-map.html">知識庫與歸檔 ↗</a><a href="#source-document">原始工法與資料 ↓</a>';
 links.querySelector('a[href="#source-document"]').onclick=()=>{document.getElementById('source-document').open=true;};
 main.querySelector('.sb-section-head h2').textContent='守住原有工法，把傳承安排落實';
 main.querySelector('.sb-source-note').textContent='圖中策略與預期成效為編者整理；新增驗收方式是待覆核建議，不是仙佛原話。原始工法、慈訓引文及歷史版本說明完整保留於下方。';
}
document.getElementById('sb-download').onclick=()=>{
location.href='system-'+d.key+'-worksheet.md'; return;
};
main.querySelectorAll('a[href$=".html"]').forEach(a=>a.setAttribute('href',a.getAttribute('href')+'?layout=tiered2'));
})();
