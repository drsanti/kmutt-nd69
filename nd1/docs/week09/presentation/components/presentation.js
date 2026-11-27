/* Slide shell and navigation. Widgets mount on demand and may return cleanup(). */
(() => {
  const $=id=>document.getElementById(id),slides=W09_CHAPTERS.flatMap((c,ci)=>c.slides.map(s=>({...s,chapter:c.name,chapterIndex:ci,source:c.source})));let index=0,cleanup=()=>{};
  const stage=$('stage'),chapters=$('chapters'),overview=$('overview'),grid=$('overview-grid');
  W09_CHAPTERS.forEach((c,i)=>chapters.append(W09.el('option',{value:i},c.name)));
  slides.forEach((s,i)=>{const b=W09.el('button',{},`${String(i+1).padStart(2,'0')} · ${s.title}${s.reference?' · reference':''}`);b.onclick=()=>{overview.close();go(i);};grid.append(b);});
  function codeBlock(code,root){const pre=W09.el('pre'),c=W09.el('code',{},code);pre.append(c);root.append(pre);const b=W09.el('button',{class:'copy'},'Copy code');b.onclick=()=>W09.copy(code,b);root.append(b);}
  function render(){cleanup();cleanup=()=>{};const s=slides[index];stage.replaceChildren();const article=W09.el('article',{class:'slide','aria-labelledby':'slide-title'}),eye=W09.el('p',{class:'eyebrow'},`${s.chapter} ${s.reference?' / Reference':''}`),h=W09.el('h1',{id:'slide-title'},s.title);article.append(eye,h);
    const layout=W09.el('div',{class:'slide-grid'+(s.demo?' has-demo':'')}),content=W09.el('div',{class:'content'});content.append(W09.el('p',{class:'lead'},s.lead));if(s.points.length){const ul=W09.el('ul',{class:'points'});s.points.forEach(p=>ul.append(W09.el('li',{},p)));content.append(ul);}if(s.code)codeBlock(s.code,content);
    if(s.quiz){const q=W09.el('div',{class:'quiz'}),feedback=W09.el('p',{class:'feedback','aria-live':'polite'});s.quiz.options.forEach((option,i)=>{const b=W09.el('button',{},option);b.onclick=()=>{q.querySelectorAll('button').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');feedback.className='feedback '+(i===s.quiz.answer?'quiz-correct':'quiz-wrong');feedback.textContent=(i===s.quiz.answer?'Correct. ':'Try again. ')+s.quiz.explanation;};q.append(b);});content.append(q,feedback);}
    layout.append(content);if(s.demo){const demo=W09.el('div',{class:'demo','data-demo':s.demo});layout.append(demo);if(!W09.widgets[s.demo])throw new Error('Missing widget: '+s.demo);cleanup=W09.widgets[s.demo](demo,s.demo)||(()=>{});}
    article.append(layout);const source=W09.el('p',{class:'source'});source.append('Source: ',W09.el('a',{href:`https://github.com/drsanti/kmutt-nd69/blob/${W09_META.courseCommit}/nd1/docs/week09/${s.source}`,target:'_blank',rel:'noopener'},s.source),' · browser simulations are illustrative unless marked repository data.');article.append(source);stage.append(article);
    $('notes-text').textContent=s.notes;chapters.value=s.chapterIndex;$('counter').textContent=`${index+1} / ${slides.length}`;$('progress-fill').style.width=`${(index+1)/slides.length*100}%`;$('previous').disabled=index===0;$('next').disabled=index===slides.length-1;const prevTop=$('topbar-prev'),nextTop=$('topbar-next'),st=$('titlebar-slide-title');if(prevTop)prevTop.disabled=index===0;if(nextTop)nextTop.disabled=index===slides.length-1;if(st)st.textContent=`${index+1}. ${s.title}`;document.title=`${index+1}. ${s.title} — ND01 Week 09`;window.scrollTo(0,0);
  }
  function go(i){index=W09.clamp(i,0,slides.length-1);const hash='#slide-'+(index+1);if(location.hash!==hash)location.hash=hash;else render();}
  function hash(){const m=location.hash.match(/^#slide-(\d+)$/);index=W09.clamp(m?Number(m[1])-1:0,0,slides.length-1);render();}
  $('next').onclick=()=>go(index+1);$('previous').onclick=()=>go(index-1);$('topbar-prev')?.addEventListener('click',()=>go(index-1));$('topbar-next')?.addEventListener('click',()=>go(index+1));chapters.onchange=()=>go(slides.findIndex(s=>s.chapterIndex===+chapters.value));$('overview-open').onclick=()=>overview.showModal();$('overview-close').onclick=()=>overview.close();$('help-open').onclick=()=>$('help').showModal();$('help-close').onclick=()=>$('help').close();$('theme').onclick=()=>{document.body.classList.toggle('dark');$('theme').setAttribute('aria-pressed',String(document.body.classList.contains('dark')));};
  async function fullscreen(){try{if(!document.fullscreenElement)await document.documentElement.requestFullscreen();else await document.exitFullscreen();}catch{$('status').textContent='Fullscreen unavailable in this browser. Use the browser’s fullscreen command.';}}
  $('fullscreen').onclick=fullscreen;
  document.addEventListener('keydown',e=>{if(document.querySelector('dialog[open]')||e.ctrlKey||e.metaKey||e.altKey||/INPUT|SELECT|TEXTAREA|BUTTON/.test(e.target.tagName)||e.target.isContentEditable)return;const k=e.key.toLowerCase();if(['arrowright','arrowdown','pagedown',' '].includes(k)){e.preventDefault();go(index+1);}else if(['arrowleft','arrowup','pageup'].includes(k)){e.preventDefault();go(index-1);}else if(k==='home'){e.preventDefault();go(0);}else if(k==='end'){e.preventDefault();go(slides.length-1);}else if(k==='f')fullscreen();else if(k==='n')$('notes').open=!$('notes').open;else if(k==='o')overview.showModal();else if(k==='?')$('help').showModal();});
  function preparePrint(){const deck=$('print-deck');deck.replaceChildren();slides.forEach((s,i)=>{const a=W09.el('article',{class:'print-slide'});a.append(W09.el('p',{},`${i+1} / 85 · ${s.chapter}`),W09.el('h1',{},s.title),W09.el('p',{},s.lead));const ul=W09.el('ul');s.points.forEach(p=>ul.append(W09.el('li',{},p)));a.append(ul);if(s.code)a.append(W09.el('pre',{},s.code));if(s.demo)a.append(W09.el('p',{},`Interactive demonstration: ${s.demo}. Open the HTML for adjustable plots; this print view is a static teaching reference.`));if(s.quiz)a.append(W09.el('p',{},`Question: ${s.quiz.options.join(' / ')}. Answer: ${s.quiz.options[s.quiz.answer]}. ${s.quiz.explanation}`));deck.append(a);});}
  $('print').onclick=()=>{preparePrint();window.print();};window.addEventListener('beforeprint',preparePrint);window.addEventListener('hashchange',hash);hash();
  const installBtn=$('install-app');let deferredPrompt=null;
  window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e;if(installBtn)installBtn.hidden=false;});
  if(installBtn){installBtn.onclick=async()=>{if(!deferredPrompt)return;deferredPrompt.prompt();const choice=await deferredPrompt.userChoice;if(choice&&choice.outcome==='accepted'&&installBtn)installBtn.hidden=true;deferredPrompt=null;};}
  window.addEventListener('appinstalled',()=>{if(installBtn)installBtn.hidden=true;const s=$('status');if(s)s.textContent='ND01 Week 09 Desktop App installed successfully.';});
  if('serviceWorker' in navigator&&(location.protocol==='https:'||location.hostname==='localhost'||location.hostname==='127.0.0.1')){
    window.addEventListener('load',()=>{navigator.serviceWorker.register('sw.js').catch(()=>{});});
  }
  // Desktop custom borderless titlebar controls (macOS style unified toolbar)
  function setupDesktopTitlebar(){
    const titlebar=$('desktop-titlebar');
    if(!titlebar)return;

    // Drag region (excluding buttons, selects, links)
    titlebar.onpointerdown=e=>{
      if(e.button!==0||e.target.closest('button, select, input, a, dialog'))return;
      if(window.Neutralino?.window?.beginDrag)Neutralino.window.beginDrag(e.screenX,e.screenY);
    };

    // Double-click to Maximize / Restore
    titlebar.ondblclick=e=>{
      if(e.target.closest('button, select, input, a, dialog'))return;
      toggleMaximize();
    };

    async function toggleMaximize(){
      if(window.Neutralino?.window){
        try{
          const isMax=await Neutralino.window.isMaximized();
          if(isMax){
            await Neutralino.window.unmaximize();
            document.body.classList.remove('is-maximized');
          }else{
            await Neutralino.window.maximize();
            document.body.classList.add('is-maximized');
          }
        }catch(err){}
      }else{
        fullscreen();
      }
    }

    $('win-min')?.addEventListener('click',()=>{
      if(window.Neutralino?.window)Neutralino.window.minimize();
    });
    $('win-max')?.addEventListener('click',toggleMaximize);
    $('win-close')?.addEventListener('click',()=>{
      if(window.Neutralino?.app)Neutralino.app.exit();
      else if(window.close)window.close();
    });

    function syncTitle(){
      const t=$('slide-title'),st=$('titlebar-slide-title');
      if(t&&st)st.textContent=`${index+1}. ${t.textContent}`;
    }
    window.addEventListener('hashchange',()=>setTimeout(syncTitle,40));
    setTimeout(syncTitle,100);
  }

  window.setupDesktopTitlebar=setupDesktopTitlebar;
  setupDesktopTitlebar();
  if(typeof Neutralino!=='undefined'||window.NL_PORT){
    if(window.Neutralino?.events){
      Neutralino.events.on('ready',setupDesktopTitlebar);
      Neutralino.events.on('windowMaximized',()=>document.body.classList.add('is-maximized'));
      Neutralino.events.on('windowUnmaximized',()=>document.body.classList.remove('is-maximized'));
    }
  }
})();
