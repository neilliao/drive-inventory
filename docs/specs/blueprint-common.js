/* Shared navigation and presentation; original source documents stay intact. */
document.addEventListener('DOMContentLoaded',()=>{
const pages=[
 ['grand','文書組總圖','2026-09-01-emei-wenshu-grand-strategy-map.html',null,'共同方向｜修己、育人、渡人'],
 ['fahui','法會文書','2026-09-01-fahui-wenshu-strategy-map.html','grand','傳承抄校工法，守住核定與歸檔'],
 ['daowu','道務文書','2026-08-17-strategy-map.html','grand','以存、找、傳、承，留下可接續的記錄'],
 ['registry','道籍系統','2026-08-20-daoji-system-strategy-map.html','daowu','提供共同的人員正本與職務依據'],
 ['library','知識庫','2026-08-20-knowledge-base-strategy-map.html','daowu','保存正本，供查找、傳達與取材'],
 ['portal','道務平台','2026-08-20-daowu-platform-implementation-map.html','daowu','銜接資料入口，讓公告可查找'],
 ['media','媒體／季刊','2026-08-20-media-strategy-map.html','daowu','整理與傳達故事，成果回存'],
 ['archive','文獻平台','2026-08-20-literature-platform-implementation-map.html','daowu','承接審核內容，累積可查找的典藏']
];
const current=pages.find(p=>location.pathname.endsWith(p[2]));if(!current)return;
const root=document.querySelector('.system-blueprint,.atlas');if(!root)return;
document.body.classList.add('blueprint-site');root.classList.add('bp-content');
const css=document.createElement('link');css.rel='stylesheet';css.href='blueprint-common.css?v=1';document.head.append(css);
root.id=root.id||'blueprint-content';
const link=p=>`<a href="${p[2]}"${p===current?' aria-current="page"':''}>${p[1]}</a>`;
const ancestors=[];let cursor=current;while(cursor){ancestors.unshift(cursor);cursor=pages.find(p=>p[0]===cursor[3]);}
const shell=document.createElement('header');shell.className='bp-shell';
shell.innerHTML=`<a class="bp-skip" href="#${root.id}">跳至藍圖內容</a><div class="bp-masthead"><a class="bp-brand" href="${pages[0][2]}"><span aria-hidden="true">文</span>峨眉文書藍圖</a><details class="bp-directory"><summary>全部藍圖</summary><nav aria-label="整體藍圖架構"><p>共同目標</p>${link(pages[0])}<p>兩套支援系統</p>${pages.slice(1,3).map(link).join('')}<p>道務細部藍圖</p>${pages.slice(3).map(link).join('')}</nav></details></div><nav class="bp-breadcrumb" aria-label="目前位置">${ancestors.map(link).join('<span aria-hidden="true">／</span>')}</nav><p class="bp-context">${current[4]}</p>`;
root.before(shell);
// Supersede only the old header nav; do not hide maps or original documents.
root.querySelector(':scope > .sb-nav,:scope > .atlas-nav')?.remove();
const footer=document.createElement('footer');footer.className='bp-footer';
const related=current[0]==='grand'?pages.slice(1,3):current[0]==='daowu'?pages.slice(3):current[0]==='fahui'?[pages[2],pages[4]]:pages.slice(3).filter(p=>p!==current);
footer.innerHTML=`<p class="bp-label">${current[0]==='grand'||current[0]==='daowu'?'往下看分工':'接著看相關藍圖'}</p><nav aria-label="相關藍圖">${related.map(p=>`<a href="${p[2]}"><strong>${p[1]} <span aria-hidden="true">↗</span></strong><small>${p[4]}</small></a>`).join('')}</nav><div class="bp-return">${current[3]?`<a href="${pages.find(p=>p[0]===current[3])[2]}">← 返回${pages.find(p=>p[0]===current[3])[1]}</a>`:''}<a href="#${root.id}">回到本頁總覽 ↑</a></div><p class="bp-disclaimer">本藍圖為規劃與編者整理；慈訓原文另列，預期成效不代表已完成。</p>`;
root.append(footer);
// Map links and the shared directory already provide these destinations.
// Keep only return/source utilities here, not a second catalogue of cards.
footer.querySelector('.bp-label')?.remove();
footer.querySelector('nav')?.remove();
// Keep the dependency explanation once; cross-page links live in the shared footer.
root.querySelector('.sb-connection nav')?.remove();
const source=document.querySelector('#source-document,#original');
if(source){const a=document.createElement('a');a.href='#'+source.id;a.textContent='原始規劃與慈訓 ↓';a.onclick=()=>{source.open=true;};footer.querySelector('.bp-return').append(a);}
// Local blueprint links must not silently switch to the older published edition.
document.querySelectorAll('a[href]').forEach(a=>{const original=a.getAttribute('href');if(original.startsWith('#'))return;const u=new URL(original,location.href);const page=pages.find(p=>u.pathname.endsWith('/'+p[2]));if(page&&(u.origin===location.origin||u.hostname==='neilliao.github.io'))a.setAttribute('href',page[2]+'?edition=unified1'+u.hash);});
});
