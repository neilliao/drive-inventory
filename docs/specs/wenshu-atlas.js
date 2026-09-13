/* Visual redesign: the established strategy and original quotations are retained.
   Illustrations communicate actions; HTML labels and connectors communicate relationships.
   Assumption: redesign the grand strategy page already in scope, not the linked sub-map. */
(() => {
 const guide = document.querySelector('.guide');
 const routes = [
  {id:'self',word:'修己',sub:'以文修己',line:'在做事中，修自己的心。',image:'伏案謹慎抄寫的文書人員',position:'0%',verbs:['靜心','充實道學','謙卑'],cycle:'事修人',cycleText:'辦事 → 省察 → 再實踐'},
  {id:'teach',word:'育人',sub:'以文育人',line:'把前人的功夫，交到後人手上。',image:'前賢陪伴後學一起研讀與練習',position:'50%',verbs:['備教材','帶著做','及早交棒'],cycle:'人傳人',cycleText:'見習 → 承擔 → 帶後學'},
  {id:'share',word:'渡人',sub:'以文渡人',line:'讓留下的話，繼續成全人。',image:'向眾人分享書中智慧',position:'100%',verbs:['及時發放','講述啟示','走入人群'],cycle:'以文為徑',cycleText:'尊重弘法、成全組的分工'}
 ];
 const root = document.createElement('main');
 root.className = 'atlas'; root.id = 'visual-blueprint';
 root.innerHTML = `
 <nav class="atlas-nav" aria-label="藍圖導覽"><a href="../index.html" class="atlas-brand"><span class="brand-seal">文</span>峨眉書院<span class="brand-divider">／</span>文書組</a><a href="#whole">完整策略圖 <span aria-hidden="true">↗</span></a></nav>
 <header class="atlas-header"><div><p class="atlas-eyebrow">一個心願・三條路・代代相傳</p><h1>峨眉文書組<span>藍圖</span></h1></div><p class="atlas-preface">讓後人得以飲水思源。<br>把道留在文字裡，也活在人身上。</p></header>
 <div class="atlas-toolbar"><p><span class="touch-dot"></span>點選圖中的一條路，看做法與慈訓</p><div class="view-controls" aria-label="看圖重點"><button type="button" data-view="all" aria-pressed="true">看全貌</button><button type="button" data-view="paths" aria-pressed="false">看三條路</button><button type="button" data-view="systems" aria-pressed="false">看分工</button></div></div>
 <section class="atlas-map" aria-label="戰略、戰術、戰技關係圖">
  <div class="goal-row"><span class="tier-label"><b>戰略</b>為什麼做</span><div class="goal-node"><span class="goal-ornament" aria-hidden="true">文</span><h2>文以載道<span>道以成全人</span></h2><p>修自己・育後人・渡眾生</p></div><div class="goal-side">同一個心願<br><span>由三條路共同實現</span></div></div>
  <div class="atlas-branches" aria-hidden="true"><svg viewBox="0 0 1000 60" preserveAspectRatio="none"><path d="M500 0V20M166 60V38Q166 20 186 20H814Q834 20 834 38V60M500 20V60"/><circle cx="500" cy="20" r="4"/></svg></div>
  <div class="paths-label"><span class="tier-label"><b>戰術</b>走哪條路</span><span>三條路彼此相助，並非先後順序</span></div>
  <div class="atlas-paths">${routes.map((r,i)=>`<button type="button" class="path-portal" data-route="${i}" aria-haspopup="dialog"><span class="path-index">0${i+1}<span>／${r.sub}</span></span><span class="path-art" style="--scene-position:${r.position}" role="img" aria-label="${r.image}"></span><span class="path-title">${r.word}<span class="portal-arrow" aria-hidden="true">↗</span></span><span class="path-description">${r.line}</span><span class="path-methods">${r.verbs.map(v=>`<span>${v}</span>`).join('')}</span><span class="portal-caption">看做法與慈訓</span></button>`).join('')}</div>
  <div class="practice-caption"><span class="tier-label"><b>戰技</b>實際怎麼做</span><p>靜心、教學、傳達，讓三條路落在日常功夫裡。</p></div>
  <div class="support-connector"><span>兩套系統，共同支持上方三條路</span></div>
  <div class="atlas-systems"><a class="system-block" href="https://neilliao.github.io/drive-inventory/specs/2026-09-01-fahui-wenshu-strategy-map.html"><span class="large-seal">信</span><div><span class="system-kicker">記天音</span><h3>法會文書</h3><p>抄錄 <span>→</span> 校對 <span>→</span> 傳承</p><small>古法只傳承，不另作設計。</small></div><span class="system-open">看藍圖 ↗</span></a><a class="system-block" href="https://neilliao.github.io/drive-inventory/specs/2026-08-17-strategy-map.html"><span class="large-seal">史</span><div><span class="system-kicker">記人事</span><h3>道務文書</h3><p>記錄 <span>→</span> 保存 <span>→</span> 找用傳</p><small>制度不繫於一人，讓後人能接手。</small></div><span class="system-open">看藍圖 ↗</span></a></div>
 </section>
 <section class="atlas-continuity" aria-label="修行與傳承的循環"><div class="continuity-intro"><span>持續做，代代傳</span><h2>事修人，<br>人傳人。</h2></div><div class="cycle-diagram"><span class="cycle-ring" aria-hidden="true">↻</span><div><h3>事修人</h3><p>辦事 → 省察 → 再實踐</p><small>做的事，回頭修做的人。</small></div></div><div class="cycle-diagram"><span class="cycle-ring" aria-hidden="true">↻</span><div><h3>人傳人</h3><p>見習 → 承擔 → 帶後學</p><small>走過的人，回頭帶下一位。</small></div></div></section>
 <footer class="atlas-footer"><span class="footer-seal" aria-hidden="true">文</span><div><p>留下文字，也傳下身教。</p><span>前人一生的示現完整留下，活著就開始寫。</span></div><button type="button" class="root-teaching">敬讀文昌帝君慈訓 ↗</button></footer>
 <dialog class="atlas-dialog" aria-labelledby="atlas-dialog-title"><div class="dialog-top"><span class="dialog-eyebrow"></span><button type="button" class="dialog-close" aria-label="關閉詳解">關閉 ×</button></div><div class="dialog-layout"><div class="dialog-art"></div><div class="dialog-content"><h2 id="atlas-dialog-title"></h2><div class="dialog-copy"></div><details class="dialog-teaching"><summary>敬讀對應慈訓與出處</summary><div class="dialog-quote"></div><p class="quote-status">沿用原頁敬錄內容；選輯覆核中，不對外發放。</p></details></div></div></dialog>`;
 guide.before(root); guide.hidden = true;
 document.querySelector('.skip').href = '#visual-blueprint';
 const dialog = root.querySelector('dialog');
 let opener;
 function openRoute(i,button) {
  const r=routes[i]; opener=button;
  root.querySelector('.dialog-eyebrow').textContent=`${String(i+1).padStart(2,'0')} ／ ${r.sub}`;
  root.querySelector('#atlas-dialog-title').textContent=r.word;
  const copy = guide.querySelector(`#${r.id} .route-body`).cloneNode(true);
  copy.querySelector('.quote-link')?.remove();
  root.querySelector('.dialog-copy').replaceChildren(copy);
  root.querySelector('.dialog-art').style.setProperty('--scene-position',r.position);
  root.querySelector('.dialog-art').hidden=false;
  const quote=document.querySelectorAll('.original-document .quotes .quote')[i].cloneNode(true);
  root.querySelector('.dialog-quote').replaceChildren(quote);
  root.querySelector('.dialog-teaching').open=false;
  dialog.showModal();
 }
 root.querySelectorAll('[data-route]').forEach(button=>button.addEventListener('click',()=>openRoute(Number(button.dataset.route),button)));
 root.querySelector('.dialog-close').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('close',()=>opener?.focus());
 dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
 root.querySelectorAll('button[data-view]').forEach(button=>button.addEventListener('click',()=>{
  root.dataset.view=button.dataset.view;
  root.querySelectorAll('button[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
 }));
 root.querySelector('.root-teaching').addEventListener('click',event=>{
  opener=event.currentTarget;
  root.querySelector('.dialog-eyebrow').textContent='文以載道・藍圖的根本';
  root.querySelector('#atlas-dialog-title').textContent='敬讀文昌帝君慈訓';
  root.querySelector('.dialog-art').hidden=true;
  root.querySelector('.dialog-copy').replaceChildren();
  const teaching=guide.querySelector('.teaching').cloneNode(true);
  teaching.open=true;
  root.querySelector('.dialog-quote').replaceChildren(teaching);
  root.querySelector('.dialog-teaching').open=true;
  dialog.showModal();
 });
})();
