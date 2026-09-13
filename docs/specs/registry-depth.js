(()=>{
if(!location.pathname.endsWith('2026-08-20-daoji-system-strategy-map.html'))return;
const main=document.querySelector('.system-blueprint');if(!main)return;
const sections=[
{id:'structure',title:'系統如何支撐日常',file:'registry-architecture-v1.png',caption:'名冊正本 → 區、組與職務 → 日常功能；同一份資料支援作業、查詢與治理。',detail:'地基是道親與佛堂名冊；治理層決定歸屬、責任與取用範圍；功能層包含求道、班程、法會、圖書、成全紀錄、懷恩祠前賢名錄。各功能共用正本，陪伴紀錄不隨一次活動結束而中斷。'},
{id:'companionship',title:'核心不是管理，而是修行關係',file:'registry-journey-v1.png',caption:'陌生人 → 善信 → 求道 → 留任 → 自願奉獻 → 辦事 → 授課；每一站都有陪伴與紀錄。',detail:'這是原頁的動線示意，依個人因緣陪伴，不是強制路線或考核階級。紀錄、授權查詢與後續關懷應形成持續陪伴；提醒功能及實際權限仍須以現行系統驗證。敏感成全紀錄不得因跨系統連結而擴大可見範圍。'},
{id:'connections',title:'讓人的正本，接起其他系統',file:'registry-connections-v1.png',caption:'道籍提供職務與受眾依據；活動與故事以共同編號回連。連線是規劃關係，不表示串接已完成。',detail:'原頁把知識庫權限名單與通知受眾列為優先銜接；場次編號互引、人物誌與故事反查列為後續。共用線索為人＝道籍編號、事＝日期與活動、理＝詞條。群組數量與即時串接狀態未在本次查核。'}
];
const block=document.createElement('section');block.className='registry-depth';block.setAttribute('aria-label','道籍架構與成全落地');
block.innerHTML=sections.map((s,i)=>`<section id="registry-${s.id}" class="registry-detail"><p class="sb-eyebrow">理解道籍 · 0${i+1}</p><h2>${s.title}</h2><figure><a href="${s.file}" target="_blank" rel="noopener" aria-label="放大：${s.title}"><img src="${s.file}" alt="${s.caption}" width="1536" height="1024" loading="lazy"></a><figcaption>${s.caption}</figcaption></figure><details><summary>閱讀關係與使用邊界</summary><p>${s.detail}</p></details></section>`).join('');
const bars=[['地基（名冊＋資料品質）',97],['班程',95],['圖書',95],['成全紀錄',95],['法會（含外部法會）',92],['求道',90],['治理駕駛艙',78],['分析層',70],['可複製給友單位',35],['能力對外輸出',5]];
block.insertAdjacentHTML('beforeend',`<aside class="registry-boundaries"><h2>兩條紅線，決定怎麼落實</h2><div><h3>不能只靠一個人維護</h3><p>各單位能維護自己的資料，接手者能依文件完成工作。</p></div><div><h3>能做到，不等於有人用</h3><p>先確認實際使用需求；少用的能力保留，不急著擴建。</p></div></aside><details class="registry-history"><summary>功能覆蓋歷史盤點 · 2026-06-18（非目前進度）</summary><p>以下沿用原頁數字，未重新驗證；不是使用成效、即時進度或驗收結果。</p>${bars.map(([name,value])=>`<div class="registry-bar"><span>${name}</span><meter min="0" max="100" value="${value}" aria-label="${name}，歷史覆蓋值 ${value}%">${value}%</meter><span>${value}%</span></div>`).join('')}<p>原頁說明：後兩項低值反映尚不過度投資，並非人員成績。</p></details><p class="sb-status">插畫與圖中文字為編者整理及示意，非訓文；人物與場景不代表真實個資或正式介面。</p>`);
main.querySelector('#sb-work').before(block);
block.querySelectorAll('figure > a').forEach(link=>{const hint=document.createElement('span');hint.textContent='點圖放大 ↗';hint.className='registry-zoom';link.append(hint);});
const connection=main.querySelector('.sb-connection');
if(connection){const explanation=connection.querySelector('p');if(explanation)block.querySelector('#registry-connections details').append(explanation);connection.remove();}
const boundaries=block.querySelector('.registry-boundaries');
boundaries.querySelector('h2').textContent='落實守則';
boundaries.querySelectorAll(':scope > div').forEach((item,i)=>{const detail=document.createElement('details');const summary=document.createElement('summary');summary.textContent=i?'有需求，再擴建':'分工維護，換人能接';detail.append(summary,item.querySelector('p'));item.replaceWith(detail);});
block.querySelector('#registry-connections figcaption').textContent='共用人的正本，串起資料與通知。連線為規劃，尚非完成。';
block.querySelector('.registry-history summary').textContent='歷史盤點 · 2026-06-18（非現況）';
block.querySelector(':scope > .sb-status').textContent='插畫為編者示意，非訓文或正式介面。';
const figure=block.querySelector('#registry-connections figure');
const zoom=figure.querySelector('a');
const frame=document.createElement('div');frame.className='registry-link-map';
figure.prepend(frame);frame.append(zoom.querySelector('img'));
zoom.setAttribute('aria-label','放大系統銜接全圖');zoom.querySelector('span').textContent='放大看全圖 ↗';
const destinations=[
 ['知識庫','2026-08-20-knowledge-base-strategy-map.html?layout=tiered2',1.5,12,28.7,32.5],
 ['公告與通知｜道務平台','2026-08-20-daowu-platform-implementation-map.html?layout=tiered2',69.8,12,28.7,32.5],
 ['活動總表｜知識庫','2026-08-20-knowledge-base-strategy-map.html?layout=tiered2',1.5,49.8,27.5,33],
 ['文獻與故事','2026-08-20-literature-platform-implementation-map.html?layout=tiered2',71,49.8,27.5,33]
];
destinations.forEach(([label,href,left,top,width,height])=>{const a=document.createElement('a');a.href=href;a.className='registry-map-link';a.setAttribute('aria-label',`前往${label}策略藍圖`);a.style.cssText=`left:${left}%;top:${top}%;width:${width}%;height:${height}%`;const tag=document.createElement('span');tag.textContent='看藍圖 ↗';a.append(tag);frame.append(a);});
// Withdraw the assistant-proposed checklist from the reader-facing registry page.
// The source document and shared data are retained, so this is reversible.
main.querySelector('#sb-work')?.remove();
main.querySelectorAll('a[href="#sb-work"]').forEach(a=>{a.href='#registry-structure';a.textContent='看系統圖解 ↓';});
const targets=['registry-structure','registry-companionship','registry-connections'];
const routeButtons=[...main.querySelectorAll('.sb-route-buttons button')];
const mapButtons=[...main.querySelectorAll('.sb-map-hit')];
routeButtons.forEach((button,i)=>{
 const label=button.textContent.replace('看落實','看圖解');
 const show=()=>{const target=document.getElementById(targets[i]);target.setAttribute('tabindex','-1');target.scrollIntoView({block:'start'});target.focus({preventScroll:true});};
 button.textContent=label;button.onclick=show;
 const hit=mapButtons[i];if(hit){hit.setAttribute('aria-label',label);hit.querySelector('span').textContent='看圖解 ↓';hit.onclick=show;}
});
const sourceNote=main.querySelector('.sb-source-note');if(sourceNote)sourceNote.textContent='圖解為編者整理；原始規劃與慈訓保留於下方，歷史進度未重新查核。';
})();
