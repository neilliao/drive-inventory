/* Graphical reading layer; original source stays available below in full.
   Stage order is a plan from the original map, not a live completion report. */
(()=>{
 const original=document.querySelector('.wrap');
 const source=document.createElement('details');source.className='original-document';source.id='original';
 source.innerHTML='<summary>慈訓、背景與原始規劃說明 ↓</summary>';
 original.before(source);source.append(original);
 const lanes=[
 {word:'存',title:'正本各歸其家',why:'資料放在哪裡？',work:'人的資料進道籍，檔案進知識庫。',result:'每份資料都有固定位置',tools:['registry','library']},
 {word:'找',title:'人、事、理都有線索',why:'需要時怎麼找到？',work:'人用編號、事用日期、理用詞條。',result:'從入口找得到所需資料',tools:['library','registry','portal']},
 {word:'傳',title:'發一次，送到需要的人',why:'誰應該收到？',work:'依受眾傳達，正式件寄信，公告留底。',result:'消息送得準，也留得住',tools:['line','mail','portal','registry','media','chant']},
 {word:'承',title:'讓紀錄成為可傳的故事',why:'後人能留下什麼？',work:'素材整理成課題、人物誌，再長久典藏。',result:'前人的示現繼續成全後人',tools:['media','archive','library','registry']}
 ];
 const tools={registry:['道籍系統','人的正本・編號・名單・足跡','2026-08-20-daoji-system-strategy-map.html'],library:['知識庫','檔案歸位・目錄・素材','2026-08-20-knowledge-base-strategy-map.html'],portal:['道務平台','查找入口・公告留底','2026-08-20-daowu-platform-implementation-map.html'],line:['LINE','推送到手機',null],mail:['信箱','寄送正式件',null],media:['媒體／季刊','對外傳達・故事整理','2026-08-20-media-strategy-map.html'],archive:['文獻平台','人物與文獻典藏','2026-08-20-literature-platform-implementation-map.html'],chant:['誦經頁','共修傳達',null]};
 const root=document.createElement('main');root.className='atlas daowu-atlas';root.innerHTML=`
 <nav class="atlas-nav" aria-label="藍圖導覽"><a class="atlas-brand" href="2026-09-01-emei-wenshu-grand-strategy-map.html"><span class="brand-seal">文</span>回峨眉文書組藍圖</a><a href="#original">完整原圖 ↗</a></nav>
 <header class="atlas-header"><div><p class="atlas-eyebrow">峨眉文書組藍圖 ／ 道務文書</p><h1>道務文書<span>藍圖</span></h1></div><p class="atlas-preface">把每天發生的事，<br>記下來、找得到、送出去、傳下去。</p></header>
 <section class="daowu-map" aria-labelledby="daowu-goal"><div class="daowu-goal"><span class="goal-stamp">史</span><div><p class="map-label">戰略・共同目標</p><h2 id="daowu-goal">為峨眉修一部活的史</h2><p>記得每一份奉獻，繼續成全後人；整套工作不繫於任何一人。</p></div></div>
 <div class="daowu-spread" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
 <div class="map-explainer"><p><b>戰術</b> 四條路，同時支持共同目標</p><span>點選一條路，查看它使用哪些工具</span><button type="button" class="clear-path" hidden>顯示全部</button></div>
 <div class="daowu-lanes">${lanes.map((l,i)=>`<article class="daowu-lane" data-lane="${i}"><button class="lane-select" type="button" data-select="${i}" aria-pressed="false"><span class="daowu-number">0${i+1}</span><strong>${l.word}</strong><span>${l.why}</span><small>看支援工具 ↓</small></button><div class="daowu-action"><span class="map-label">實際做法</span><h3>${l.title}</h3><p>${l.work}</p></div><div class="daowu-outcome"><span class="map-label">預期成果</span><p>${l.result}</p></div></article>`).join('')}</div>
 <section class="tools-layer" aria-labelledby="tools-title"><div class="tools-heading"><div><p class="map-label">戰技・工具如何支援</p><h3 id="tools-title">一個工具，可以支援多條路</h3></div><p class="tool-state" aria-live="polite">目前顯示全部工具與對應策略</p></div><div class="tool-network">${Object.entries(tools).map(([id,t])=>`<article class="tool-node" data-tool="${id}"><div><h4>${t[0]}</h4><p>${t[1]}</p></div><div class="tool-routes" aria-label="支援的策略">${lanes.map((l,i)=>l.tools.includes(id)?`<span data-for-lane="${i}">${l.word}</span>`:'').join('')}</div>${t[2]?`<a href="${t[2]}">看細部藍圖 ↗</a>`:''}</article>`).join('')}</div><p class="tools-note">道籍系統支援四條路，提供人的正本、編號與名單；工具可以換代，存、找、傳、承的方向不變。</p></section></section>
 <section class="activity-flow"><div class="subsection-title"><span>01</span><div><p class="map-label">用一場活動，看懂資料怎麼走</p><h2>今天留下的紀錄，如何走到後人手上？</h2></div></div><ol>${[['活動發生','照片・紀錄產生'],['知識庫','歸檔・固定位置'],['道務平台','找到・取用'],['LINE＋信箱','送達・公告留底'],['季刊與文獻平台','寫成故事・長久保存']].map((x,i)=>`<li><span>${i+1}</span><h3>${x[0]}</h3><p>${x[1]}</p></li>`).join('')}</ol><p class="flow-note">共同支援：道籍系統提供身分、名單與權限依據。</p></section>
 <section class="daowu-plan"><div class="subsection-title"><span>02</span><div><p class="map-label">落實順序</p><h2>先整理，再接入，逐步成為可用的系統</h2></div></div><p class="plan-note">依原藍圖規劃排列，並非即時進度。原頁的粗估百分比保留於完整原圖。</p><ol>${[['整理知識庫','開碟、搬檔、處理個資、配置權限','檔案有家'],['道務平台接入','連接資料、設權限，再開放入口','資料找得到'],['策展與典藏','先選第一批內容，再建文獻平台','故事傳下去'],['全部連結','道籍與知識庫互相連結','人事可對照']].map((s,i)=>`<li><span class="plan-step">${i+1}</span><h3>${s[0]}</h3><p>${s[1]}</p><strong>${s[2]}</strong></li>`).join('')}</ol></section>
 <section class="daowu-rules"><div><h2>共同守住的原則</h2><ul><li>交接文件要讓沒參與過的人也能接手。</li><li>文書整理時間應減少；增加時，回頭改善系統。</li><li>權限跟著職務走，個資由系統管理。</li></ul></div><div><h2>持續改善的兩個循環</h2><p><b>依使用調整投入</b><br>看使用情況 → 常用的做深 → 少用的保留不擴建</p><p><b>維持資料秩序</b><br>巡檢 → 整理既有問題 → 改善問題來源</p></div></section>
 <p class="fahui-boundary">法會文書另冊傳承，訓文歸檔於 202 文史。</p>
 <footer class="atlas-footer"><span class="footer-seal">史</span><div><p>讓後人得以飲水思源。</p><span>前人一生的示現，活著時就一筆一筆留下。</span></div><a href="#original">敬讀原頁慈訓與完整說明 ↗</a></footer>`;
 source.before(root);
 root.querySelector('.plan-note').textContent='依原藍圖規劃排列，並非即時進度；原頁粗估百分比尚未重新核實。';
 original.querySelector('header.page')?.remove();
 original.querySelectorAll('figure.map').forEach(f=>{const p=f.previousElementSibling;if(p?.matches('p'))p.remove();const h=f.previousElementSibling;if(h?.matches('h2'))h.remove();f.remove();});
 root.querySelector('.atlas-nav>a:last-child').textContent='慈訓與補充資料 ↗';
 function select(index){root.querySelectorAll('[data-select]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.select)===index)));root.querySelectorAll('[data-lane]').forEach(a=>a.classList.toggle('lane-muted',index!==null&&Number(a.dataset.lane)!==index));root.querySelectorAll('[data-tool]').forEach(a=>{a.hidden=index!==null&&!lanes[index].tools.includes(a.dataset.tool);});root.querySelector('.clear-path').hidden=index===null;root.querySelector('.tool-state').textContent=index===null?'目前顯示全部工具與對應策略':`「${lanes[index].word}」由以下 ${lanes[index].tools.length} 項工具支援`};
 root.querySelectorAll('[data-select]').forEach(b=>b.addEventListener('click',()=>select(Number(b.dataset.select))));root.querySelector('.clear-path').addEventListener('click',()=>select(null));
 root.querySelectorAll('a[href="#original"]').forEach(a=>a.addEventListener('click',()=>source.open=true));if(location.hash==='#original')source.open=true;
 document.querySelectorAll('a[href]').forEach(a=>{if(a.href.endsWith('/specs/2026-09-01-emei-wenshu-grand-strategy-map.html'))a.setAttribute('href','2026-09-01-emei-wenshu-grand-strategy-map.html');});
})();
