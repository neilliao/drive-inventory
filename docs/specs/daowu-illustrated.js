/* Illustrated reading layer. Original quotations remain in the source disclosure. */
(()=>{
 const root=document.querySelector('.daowu-atlas');
 if(!root)return;
 const lanes=Array.from(root.querySelectorAll('.daowu-lane')).map(el=>({
  word:el.querySelector('strong').textContent,
  title:el.querySelector('.daowu-action h3').textContent,
  work:el.querySelector('.daowu-action p').textContent,
  result:el.querySelector('.daowu-outcome p').textContent
 }));
 const toolNodes=Array.from(root.querySelectorAll('.tool-node'));
 toolNodes.forEach(n=>{const a=n.querySelector('a');if(a){const u=new URL(a.getAttribute('href'),location.href);if(u.pathname.includes('/specs/'))a.setAttribute('href',u.pathname.split('/specs/')[1]+'?layout=tiered2');}});
 const planSteps=Array.from(root.querySelectorAll('.daowu-plan li')).map(el=>({title:el.querySelector('h3').textContent,work:el.querySelector('p').textContent,result:el.querySelector('strong').textContent}));
 const map=root.querySelector('.daowu-map');map.className='daowu-illustrated-map';map.removeAttribute('aria-labelledby');map.setAttribute('aria-label','道務文書策略地圖');
 map.innerHTML=`<p class="di-hint">點圖中的「存、找、傳、承」，看做法與支援工具。</p><div class="di-canvas"><img src="daowu-illustrated-map.png" width="1536" height="1024" alt="四條路共同支持為峨眉修一部活的史：存讓資料有固定位置，找讓需要時找得到，傳讓消息送達並留底，承讓前人示現傳後人。八項工具共同支援，並非四個先後步驟。">${lanes.map((l,i)=>`<button class="di-hotspot" style="left:${[1.6,26.2,50.5,74.9][i]}%;top:26.2%;width:23.3%;height:47%" data-di-route="${i}" aria-haspopup="dialog" aria-label="${l.word}：查看做法與工具"><span>看${l.word}詳解 ↗</span></button>`).join('')}<button class="di-hotspot di-tools-hotspot" style="left:31.8%;top:79%;width:36.5%;height:14%" data-di-tools aria-haspopup="dialog" aria-label="查看八項支援工具"><span>看工具分工 ↗</span></button></div><p class="di-note">圖中文字為編者整理，預期成效為規劃方向，非仙佛原話或即時進度。</p><div class="di-utilities"><a href="daowu-illustrated-map.png" target="_blank" rel="noopener">放大看全圖 ↗</a><button data-di-tools aria-haspopup="dialog">工具與細部藍圖 ↗</button></div><details class="di-mobile"><summary>開啟四條路詳解</summary><div>${lanes.map((l,i)=>`<button data-di-route="${i}" aria-haspopup="dialog">${l.word}・${l.title} ↗</button>`).join('')}</div></details>`;
 map.querySelector('.di-canvas>img').src='daowu-tiered-v4.png';
 map.querySelector('.di-canvas>img').alt='由上往下看部署：共同目標為峨眉修一部活的史；存、找、傳、承四項並行策略，下接具體行動，再由道籍、知識庫、道務平台、媒體季刊、文獻平台共同支援。左右為共同原則與改善回饋。預期成效非已完成成果。';
 map.querySelector('.di-utilities>a').href='daowu-tiered-v4.png';
 const routeBoxes=[[14.2,29.5,16.3,23],[31.4,29.5,16.2,23],[48.5,29.5,16.3,23],[65.6,29.5,16.2,23]];
 map.querySelectorAll('.di-canvas [data-di-route]').forEach((b,i)=>{const [left,top,width,height]=routeBoxes[i];b.style.cssText=`left:${left}%;top:${top}%;width:${width}%;height:${height}%`;});
 map.querySelector('.di-tools-hotspot').remove();
 const systemIds=['registry','library','portal','media','archive'];
 systemIds.forEach((id,i)=>{const node=toolNodes.find(el=>el.dataset.tool===id);const a=document.createElement('a');a.className='di-hotspot di-system-link';a.href=node.querySelector('a').getAttribute('href');a.setAttribute('aria-label','進入'+node.querySelector('h4').textContent+'細部藍圖');a.style.cssText=`left:${11.3+i*14.3}%;top:80%;width:14%;height:15.5%`;a.innerHTML='<span>進入細部藍圖 ↗</span>';map.querySelector('.di-canvas').append(a);});
 const mobileSystems=document.createElement('details');mobileSystems.className='di-mobile';mobileSystems.innerHTML='<summary>開啟五份系統藍圖</summary><div>'+systemIds.map(id=>{const node=toolNodes.find(el=>el.dataset.tool===id);return `<a href="${node.querySelector('a').getAttribute('href')}">${node.querySelector('h4').textContent} ↗</a>`;}).join('')+'</div>';map.append(mobileSystems);
 const dialog=document.createElement('dialog');dialog.className='di-dialog';dialog.setAttribute('aria-labelledby','di-dialog-title');dialog.innerHTML='<button class="di-close" aria-label="關閉道務詳解">關閉 ×</button><h2 id="di-dialog-title"></h2><div class="di-dialog-copy"></div>';
 root.append(dialog);let opener;
 const close=()=>dialog.close();dialog.querySelector('.di-close').addEventListener('click',close);dialog.addEventListener('close',()=>opener?.focus());
 dialog.addEventListener('click',event=>{if(event.target!==dialog)return;const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)close();});
 function openTools(button,index){opener=button;const lane=lanes[index];dialog.querySelector('h2').textContent=`${lane.word}｜${lane.title}`;const copy=dialog.querySelector('.di-dialog-copy');copy.replaceChildren();
  if(lane){const intro=document.createElement('p');intro.textContent=lane.work;copy.append(intro);const result=document.createElement('p');result.className='di-result';result.textContent='預期成效（編者整理）：'+lane.result;copy.append(result);}
  if(index===2){const channels=document.createElement('p');channels.textContent='傳達分工：LINE 推送、信箱寄正式件、誦經頁供共修；公告由平台留底。';copy.append(channels);}
  const list=document.createElement('nav');list.className='di-route-links';list.setAttribute('aria-label','相關細部策略圖');toolNodes.filter(el=>systemIds.includes(el.dataset.tool)&&el.querySelector(`[data-for-lane="${index}"]`)).forEach(el=>{const a=document.createElement('a');a.href=el.querySelector('a').getAttribute('href');a.textContent=el.querySelector('h4').textContent+'・看落實 ↗';list.append(a);});copy.append(list);dialog.showModal();dialog.scrollTop=0;
 }
 root.querySelectorAll('[data-di-route]').forEach(b=>b.addEventListener('click',()=>openTools(b,Number(b.dataset.diRoute))));root.querySelectorAll('[data-di-tools]').forEach(b=>b.remove());
 const plan=root.querySelector('.daowu-plan');plan.className='di-plan';plan.innerHTML=`<h2>先整理，再接通，逐步落實</h2><p class="di-hint">規劃順序，非即時進度。點場景看這一步。</p><div class="di-plan-scenes">${planSteps.map((s,i)=>`<button data-di-step="${i}" aria-expanded="false" aria-controls="di-step-detail"><span class="di-step-painting" style="--position:${i*100/3}%" aria-hidden="true"></span><strong>${s.title}</strong></button>`).join('')}</div><details id="di-step-detail"><summary>查看落實說明</summary><div class="di-step-copy" aria-live="polite">依原藍圖順序推進，實際安排仍須確認。</div></details>`;
 const stepDetail=plan.querySelector('details');let selectedStep=null;plan.querySelectorAll('[data-di-step]').forEach(b=>b.addEventListener('click',()=>{selectedStep=Number(b.dataset.diStep);const s=planSteps[selectedStep];plan.querySelector('.di-step-copy').textContent=`${s.title}：${s.work}。預計形成：${s.result}。`;stepDetail.open=true;plan.querySelectorAll('[data-di-step]').forEach(x=>x.setAttribute('aria-expanded',String(x===b)));stepDetail.querySelector('summary').focus();}));stepDetail.addEventListener('toggle',()=>plan.querySelectorAll('[data-di-step]').forEach(b=>b.setAttribute('aria-expanded',String(stepDetail.open&&Number(b.dataset.diStep)===selectedStep))));
 const extra=document.createElement('details');extra.className='di-background';extra.innerHTML='<summary>資料如何流動、共同原則與持續改善</summary><p>一場活動留下照片與紀錄，歸檔後由平台提供查找，依受眾傳達，再選材寫成故事典藏。道籍提供身分、名單與權限依據。</p><p>交接要讓後人能接手；整理時間應減少；權限跟職務走，個資由系統管理。</p><p>依使用情況調整投入，常用的做深，少用的保留不擴建；定期巡檢，整理問題並改善來源。</p>';root.querySelector('.activity-flow').remove();root.querySelector('.daowu-rules').remove();plan.after(extra);
 root.querySelector('.atlas-footer').classList.add('di-footer');
 // The overview ends at the map. Retain supplementary implementation notes only inside the source disclosure.
 const source=document.getElementById('original');
 if(source){const archive=document.createElement('details');archive.className='di-background';archive.innerHTML='<summary>補充實施順序與資料流（舊版說明）</summary>';archive.append(plan,extra);source.append(archive);}else{plan.remove();extra.remove();}
 root.querySelectorAll('a[href="#original"]').forEach(a=>a.addEventListener('click',event=>{event.preventDefault();const source=document.getElementById('original');source.open=true;source.scrollIntoView({block:'start'});history.replaceState(null,'','#original');}));
 // Supplement remains the verbatim source; no generated words are presented as scripture.
 document.querySelectorAll('a[href^="https://neilliao.github.io/drive-inventory/specs/"]').forEach(a=>{a.setAttribute('href',a.getAttribute('href').split('/specs/')[1]);});
})();
