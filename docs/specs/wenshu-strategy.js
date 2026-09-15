/* Read from the grand map, the 2026-08-17 daowu map and the 2026-09-02
   training draft. This is a planning map, not live progress or a scorecard. */
(() => {
 const atlas=document.querySelector('.atlas');
 if(!atlas)return;
 const oldMap=atlas.querySelector('.atlas-map');
 const oldPortals=Array.from(oldMap.querySelectorAll('[data-route]'));
 const rows=[
  {word:'修己',question:'做事的人如何成長？',methods:['靜心抄訓','充實道學','省察言行'],support:'法會抄校、道務辦事',result:'人在辦事中受成全',description:'細心辦事，也讓所學落在言行。'},
  {word:'育人',question:'後來的人如何接棒？',methods:['整理傳承教材','跟班見習與培訓','及早準備接棒'],support:'傳承包、法會與道務雙軌見習',result:'經驗有人接，手藝傳下去',description:'有教材可依，也有前賢陪著學。'},
  {word:'渡人',question:'文字如何成全眾生？',methods:['訓文及時發放','擷取啟示與講述','走入人群'],support:'訓文傳達、季刊與文獻內容',result:'留下的話繼續啟發人',description:'從保存、閱讀，到分享與實踐。'}
 ];
 const map=document.createElement('section');map.className='strategy-sheet';map.setAttribute('aria-label','策略與落實對照資訊圖');
 map.innerHTML=`
 <div class="strategy-mission"><span class="map-section-number">01</span><div><p class="map-overline">共同目標｜戰略</p><h2>文以載道，道以成全人</h2><p>讓後人得以飲水思源</p></div><span class="mission-seal" aria-hidden="true">文</span></div>
 <div class="mission-spread" aria-hidden="true"><span></span><span></span><span></span></div>
 <div class="logic-intro"><p><b class="read-direction">順著箭頭讀</b>：選擇的路 → 每天做的事 → 希望成就的樣貌</p><span>三條路同時相助，並非先後階段</span></div>
 <div class="logic-head" aria-hidden="true"><span>戰術<span>選擇哪條路</span></span><span>戰技與支援<span>實際怎麼落實</span></span><span>預期成效<span>希望帶來什麼改變</span></span></div>
 <div class="strategy-lanes">${rows.map((r,i)=>`<article class="strategy-lane"><button class="strategy-route" type="button" data-open-route="${i}" aria-haspopup="dialog"><span class="lane-count">0${i+1}</span><h3>${r.word}</h3><span>${r.question}</span><small>做法・慈訓 ↗</small></button><div class="lane-work"><p class="mobile-column-label">實際怎麼做</p><div class="work-nodes">${r.methods.map((m,j)=>`<span><i>${j+1}</i>${m}</span>`).join('')}</div><p class="lane-support"><span>支援</span>${r.support}</p></div><div class="lane-result"><p class="mobile-column-label">希望帶來的改變</p><span class="result-marker" aria-hidden="true">◎</span><h4>${r.result}</h4><p>${r.description}</p></div></article>`).join('')}</div>
 <div class="system-foundation"><div class="foundation-heading"><span class="map-overline">共同支援</span><h3>兩套系統，各守本位</h3><p>它們是落實的方法，共同服務修己、育人與渡人。</p></div><a href="https://neilliao.github.io/drive-inventory/specs/2026-09-01-fahui-wenshu-strategy-map.html"><span class="foundation-seal">信</span><div><h4>法會文書</h4><p>記天音・傳抄校手藝</p><small>古法只傳承，不另作設計。</small></div><span aria-hidden="true">↗</span></a><a href="https://neilliao.github.io/drive-inventory/specs/2026-08-17-strategy-map.html"><span class="foundation-seal">史</span><div><h4>道務文書</h4><p>記人事・存、找、傳、承</p><small>制度不繫於一人，後人也能接手。</small></div><span aria-hidden="true">↗</span></a></div>
 </section>`;
 // The approved illustrated map replaces the former matrix, not an extra section.
 map.classList.add('illustrated-strategy');
 map.innerHTML=`<p class="illustrated-instructions">由下往上讀：支援系統 → 具體行動 → 預期成效 → 共同目標。點選圖中的修己、育人、渡人看詳解，點兩套系統進入各自藍圖。</p>
 <div class="illustrated-canvas">
 <img src="wenshu-strategy-illustrated-v2.png" width="1536" height="1024" alt="峨眉文書組策略地圖：法會文書與道務文書共同支援修己、育人、渡人，透過九項具體行動，朝向文以載道、道以成全人的共同目標；辦事與省察互相回饋，見習、承擔、帶後學持續傳承。詳細文字可於下方展開。">
 ${rows.map((r,i)=>`<button class="map-hotspot route-hotspot" style="left:${[15.7,38.1,60.9][i]}%;top:30%;width:21%;height:19%" type="button" data-open-route="${i}" aria-label="${r.word}：查看做法、預期成效說明與慈訓" aria-haspopup="dialog"><span>看${r.word}詳解 ↗</span></button>`).join('')}
 <a class="map-hotspot system-hotspot" style="left:12.9%;top:81.7%;width:34.6%;height:13.4%" href="2026-09-01-fahui-wenshu-strategy-map.html?layout=fahui1" aria-label="進入法會文書藍圖"><span>進入法會文書 ↗</span></a>
 <a class="map-hotspot system-hotspot" style="left:48.7%;top:81.7%;width:33.4%;height:13.4%" href="2026-08-17-strategy-map.html?layout=tiered2" aria-label="進入道務文書藍圖"><span>進入道務文書 ↗</span></a>
 </div>
 <p class="illustrated-source-note">預期成效為依訓意整理的規劃方向，不是仙佛原話，也不是已完成的成果。慈訓原文與編者說明分開呈現。</p>
 <nav class="illustrated-links" aria-label="策略地圖閱讀入口">${rows.map((r,i)=>`<button type="button" data-open-route="${i}" aria-haspopup="dialog">${r.word}・做法與慈訓 ↗</button>`).join('')}<a href="2026-09-01-fahui-wenshu-strategy-map.html">法會文書 ↗</a><a href="2026-08-17-strategy-map.html">道務文書 ↗</a><a href="wenshu-strategy-illustrated-v2.png" target="_blank" rel="noopener">放大看全圖 ↗</a></nav>
 <details class="illustrated-reading"><summary>展開策略地圖文字說明</summary><p>共同目標：文以載道，道以成全人，讓後人得以飲水思源。三條路彼此相助，並非先後階段。</p>${rows.map(r=>`<p><b>${r.word}</b>：${r.methods.join('、')}。支援：${r.support}。規劃希望：${r.result}。</p>`).join('')}<p>法會文書記天音、傳承抄校手藝；道務文書記人事，支持存、找、傳、承。共同原則：修己不誤事、尊重各組分工、古法只傳承、制度不繫一人。</p><p>回饋：辦事帶來省察，省察回到辦事；見習後承擔，承擔後帶後學，持續傳承。</p></details>`;
 oldMap.before(map);oldMap.hidden=true;
 // The illustrated map is the primary navigation; keep a compact mobile fallback.
 atlas.querySelector('.view-controls')?.remove();
 const readingLinks=map.querySelector('.illustrated-links');
 const enlargeLink=readingLinks.querySelector('a[target="_blank"]');
 const mobileEntries=document.createElement('details');mobileEntries.className='mobile-map-entries';
 mobileEntries.innerHTML='<summary>開啟各項詳解</summary>';
 readingLinks.before(mobileEntries);
 mobileEntries.append(readingLinks);
 const mapUtilities=document.createElement('div');mapUtilities.className='map-utilities';mapUtilities.append(enlargeLink);
 mobileEntries.after(mapUtilities);
 const artwork=document.createElement('section');
 artwork.className='strategy-artwork';artwork.setAttribute('aria-label','修己、育人、渡人的場景圖解');
 artwork.innerHTML=`<div class="artwork-heading"><p class="map-overline">道如何落在人身上</p><p>從這三個場景，看見文書工作的心意。</p></div><div class="artwork-routes">${rows.map((r,i)=>`<button type="button" data-art-route="${i}" aria-haspopup="dialog"><span class="path-art" style="--scene-position:${i*50}%" role="img" aria-label="${['伏案修習','前賢帶後學','向眾人分享'][i]}"></span><strong>${r.word}</strong><span>${r.question}</span><small>看做法與慈訓 ↗</small></button>`).join('')}</div>`;
 map.before(artwork);
 function openIllustratedRoute(i,b){
  visibleTrigger=b;oldPortals[i].click();
  const note=document.createElement('p');note.className='outcome-editor-note';
  note.textContent=[
   '圖中「辦事更細心，言行更合道」是編者依訓意整理的預期成效，不是仙佛原話。參照《聖佛綸音・文書篇》（南極仙翁・2012年馬來西亞霹靂州怡保明龍慈軒三天法會；文昌帝君・2014年泰國昔剎吉府明修壇）分別談稱職文書與言行合道。',
   '圖中「後學能承擔，傳承有人接」是編者依訓意整理的預期成效，不是仙佛原話。參照《聖佛綸音・文書篇》（濟公活佛・2014年泰國北欖府奉恩樓）談及早交棒與準備傳承。',
   '圖中「文字被理解，啟示能實踐」是編者依訓意延伸的規劃期待，不是仙佛原話。參照《聖佛綸音・文書篇》（濟公活佛・2014年馬來西亞古晉天慈堂；濟公活佛、圓滿小仙童・2010年泰國曼谷承德壇三天法會暨二天複習班）談以聖訓作修辦準繩、引導眾生與渡人成全。'
  ][i];atlas.querySelector('.dialog-copy').prepend(note);
 }
 artwork.querySelectorAll('[data-art-route]').forEach(b=>b.addEventListener('click',()=>openIllustratedRoute(Number(b.dataset.artRoute),b)));
 map.querySelectorAll('[data-open-route]').forEach(b=>b.addEventListener('click',()=>openIllustratedRoute(Number(b.dataset.openRoute),b)));
 // Restore focus to the visible trigger, rather than its retained hidden source.
 let visibleTrigger;
 map.addEventListener('click',e=>{const trigger=e.target.closest('[data-open-route]');if(trigger)visibleTrigger=trigger;});
 atlas.querySelector('dialog').addEventListener('close',()=>{if(visibleTrigger){visibleTrigger.focus();visibleTrigger=null;}});
 const rollout=document.createElement('section');rollout.className='implementation-sheet';rollout.id='implementation';
 rollout.innerHTML=`
 <header class="implementation-header"><span class="map-section-number">02</span><div><p class="map-overline">落實路徑</p><h2>人怎麼培育，事情怎麼推進？</h2></div></header>
 <p class="implementation-note">以下依原藍圖呈現規劃順序，並非即時進度；育才路徑仍為草稿待覆核。</p>
 <section class="people-track" aria-labelledby="people-track-title"><div class="track-heading"><span class="track-letter">人</span><div><h3 id="people-track-title">從幫忙，到回頭帶人</h3><p>由帶人的前賢邀請與陪伴，按每個人的因緣往前走。</p></div><a href="https://neilliao.github.io/drive-inventory/specs/2026-09-02-wenshu-training-path.html">育才路徑詳圖 ↗</a></div>
 <ol class="people-stages">${[['幫忙','掛號、佈置、發本子'],['見習','法會／道務雙軌跟班'],['承擔','正式分工、獨立成稿'],['深化','道學充實、抄訓修心'],['轉化','講述啟示、走入人群'],['傳承','帶見習、準備接棒']].map((s,i)=>`<li><span class="stage-dot">${i}</span><h4>${s[0]}</h4><p>${s[1]}</p></li>`).join('')}</ol><div class="people-return"><span aria-hidden="true">↶</span><p>傳承的人回頭帶見習，下一代接著走。</p></div><p class="track-boundary">幫忙階段不經手錄音與訓文檔；階段由帶人者判斷，不作考核分數。</p></section>
 <section class="work-track" aria-labelledby="work-track-title"><div class="track-heading"><span class="track-letter">事</span><div><h3 id="work-track-title">道務系統，先備內容，再逐步接通</h3><p>有依存關係的四步，沿用原道務文書藍圖的順序。</p></div><a href="https://neilliao.github.io/drive-inventory/specs/2026-08-17-strategy-map.html">道務文書詳圖 ↗</a></div>
 <ol class="build-stages">${[
 ['整理知識庫','開碟、搬檔、處理個資與權限','檔案有固定位置'],
 ['接入道務平台','接資料、設權限，再開放入口','使用者找得到資料'],
 ['策展與典藏','先選內容、說故事，再建文獻平台','前人的示現被讀到'],
 ['系統互相連結','道籍與知識庫連結','人、事與紀錄能相互查找']
 ].map((s,i)=>`<li><div class="build-step"><span>${i+1}</span><h4>${s[0]}</h4></div><p>${s[1]}</p><div class="build-result"><small>預計形成</small><strong>${s[2]}</strong></div></li>`).join('')}</ol>
 <p class="ongoing-work">持續進行：季刊出刊、道籍系統鞏固；知識庫上線後再接每月巡檢。</p></section>
 <details class="planning-boundary"><summary>哪些已是方向，哪些還需拍板？</summary><div><p><b>已確立的方向：</b>修己、育人、渡人；法會文書與道務文書分工；讓後人得以飲水思源。</p><p><b>仍需覆核：</b>育才路徑草案、《聖佛綸音・文書篇》選輯。</p><p><b>仍待逐格拍板：</b>會議紀錄的執筆、成稿模板節奏、把關、傳達安排。</p><p>本圖的成效說明是便於理解的編者整理，不是訓文，也不代表工作已完成。</p></div></details>`;
 const peopleDetails=rollout.querySelector('.people-track');
 const pendingDetails=rollout.querySelector('.planning-boundary');
 peopleDetails.innerHTML='<p>由前賢邀請與陪伴，按各人的因緣參與。幫忙階段不經手錄音與訓文檔；階段由帶人者判斷，不作考核分數。</p><a href="2026-09-02-wenshu-training-path.html">查看完整育才藍圖（草案） ↗</a>';
 peopleDetails.removeAttribute('aria-labelledby');
 rollout.classList.add('compact-participation');
 rollout.innerHTML='<h2>從幫忙開始，走到回頭帶人</h2><p class="participation-stages" aria-label="培育路徑草案">幫忙 <span>→</span> 見習 <span>→</span> 承擔 <span>→</span> 深化 <span>→</span> 轉化 <span>→</span> 傳承</p><details class="participation-details"><summary>了解如何參與 <small>培育草案</small></summary></details>';
 rollout.querySelector('.participation-details').append(peopleDetails);
 document.querySelector('.original-document .wrap').prepend(pendingDetails);
 const journey=document.createElement('div');journey.className='cultivation-journey';
 journey.innerHTML=`${['幫忙','見習','承擔','深化','轉化','傳承'].map((label,i)=>`<button type="button" class="journey-scene" data-stage="${i}" aria-label="${label}：展開培育草案" aria-expanded="false" aria-controls="participation-content"><span class="journey-painting" style="--journey-position:${i*20}%" aria-hidden="true"></span><strong>${label}</strong></button>`).join('')}`;
 rollout.querySelector('.participation-stages').replaceWith(journey);
 const participation=rollout.querySelector('.participation-details');participation.id='participation-content';
 const stageNotes=['幫忙：掛號、佈置、發本子；此階段不經手錄音與訓文檔。','見習：由前賢陪伴，參與法會或道務的跟班學習。','承擔：正式分工，練習獨立成稿。','深化：充實道學，在抄訓與辦事中省察自己。','轉化：講述所體會的啟示，走入人群。','傳承：陪伴見習的後學，及早準備接棒。'];
 const stageNote=document.createElement('p');stageNote.className='selected-stage-note';stageNote.setAttribute('aria-live','polite');peopleDetails.prepend(stageNote);
 journey.querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>{stageNote.textContent=stageNotes[Number(button.dataset.stage)];participation.open=true;participation.querySelector('summary').focus();}));
 participation.addEventListener('toggle',()=>journey.querySelectorAll('button').forEach(button=>button.setAttribute('aria-expanded',String(participation.open))));
 const teachingFooter=atlas.querySelector('.atlas-footer');
 teachingFooter.classList.add('illustrated-teaching');
 const teachingButton=teachingFooter.querySelector('.root-teaching');
 const teachingImage=document.createElement('img');teachingImage.src='wenshu-teaching-entrance.png';teachingImage.alt='書卷筆墨與前賢陪伴後學的身教場景';teachingImage.width=2172;teachingImage.height=724;
 teachingImage.loading='lazy';teachingImage.decoding='async';
 const teachingCaption=document.createElement('span');teachingCaption.className='teaching-caption';teachingCaption.innerHTML='<strong>文以載道</strong><span>敬讀文昌帝君慈訓 ↗</span>';
 teachingButton.replaceChildren(teachingImage,teachingCaption);teachingButton.setAttribute('aria-haspopup','dialog');
 teachingFooter.replaceChildren(teachingButton);
 oldMap.after(rollout);
 atlas.querySelector('.atlas-continuity')?.remove();
 atlas.querySelector('.atlas-toolbar>p').innerHTML='<span class="touch-dot"></span>點圖看做法與慈訓，點系統進入各自藍圖';
 atlas.querySelector('.atlas-preface').innerHTML='從共同心願，到具體行動。<br>看懂為什麼做，也看見如何落實。';
 atlas.querySelectorAll('button[data-view]').forEach(button=>button.addEventListener('click',()=>{
  map.dataset.focus=button.dataset.view;
 }));
 // Replace the former diagram display, retaining quotations and background below.
 const supplement=document.querySelector('.original-document');
 supplement.querySelector('summary').textContent='慈訓、傳承背景與補充資料';
 supplement.querySelector('header.page')?.remove();
 const figure=supplement.querySelector('figure.map');
 if(figure){const caption=figure.previousElementSibling;if(caption?.matches('p'))caption.remove();const heading=figure.previousElementSibling;if(heading?.matches('h2'))heading.remove();figure.remove();}
 const back=document.createElement('p');back.className='supplement-return';back.innerHTML='<a href="#visual-blueprint">↑ 回到圖像與策略總覽</a>';supplement.querySelector('.wrap').prepend(back);
 atlas.querySelector('.atlas-nav>a:last-child').textContent='慈訓與補充資料 ↗';
 // Keep the two redesigned pages in the same preview/deployment origin.
 const localPages=['2026-08-17-strategy-map.html','2026-09-01-fahui-wenshu-strategy-map.html','2026-09-02-wenshu-training-path.html','2026-08-20-map-legend.html','2026-09-02-emei-wenshu-panorama.html'];
 document.querySelectorAll('a[href]').forEach(a=>{const page=localPages.find(name=>a.href.endsWith('/specs/'+name));if(page)a.setAttribute('href',page);});
})();
