W09.widgets.gesture=(root)=>{
  const {controls,out}=W09.panel(root,'Illustrative probability scores · no trained model loaded · highlight rule only');
  const preset=W09.select(controls,'Preset',['idle','shake','circle','lift','ambiguous'],presetChange);
  const threshold=W09.range(controls,'Detection threshold',0,1,.01,.7,draw);
  const names=['idle','shake','circle','lift'];
  const sliders=names.map((n,i)=>W09.range(controls,n+' score',0,1,.01,i===0?.8:.0667,draw));
  const canvas=W09.canvas(root,760,260,'Probability bars with threshold line; tap bars to change threshold');
  const presets={idle:[.8,.08,.07,.05],shake:[.04,.84,.08,.04],circle:[.05,.12,.78,.05],lift:[.1,.04,.06,.8],ambiguous:[.55,.3,.1,.05]};
  function presetChange(){presets[preset.value].forEach((v,i)=>{sliders[i].value=v;sliders[i].previousSibling.textContent=String(v);});draw();}
  function draw(){const raw=sliders.map(s=>+s.value),sum=raw.reduce((a,b)=>a+b,0),p=sum?raw.map(v=>v/sum):[.25,.25,.25,.25],thr=+threshold.value,result=W09.decision(p,thr),top=p.indexOf(Math.max(...p)),c=canvas.getContext('2d');
    c.fillStyle='#0b1930';c.fillRect(0,0,760,260);p.forEach((v,i)=>{c.fillStyle=result===names[i]?'#ffb65a':'#47bdd8';c.fillRect(90+i*160,210-v*175,90,v*175);c.fillStyle='white';c.font='16px system-ui';c.fillText(names[i],100+i*160,238);c.fillText(v.toFixed(3),100+i*160,202-v*175);});c.strokeStyle='#ffdf70';c.beginPath();c.moveTo(60,210-thr*175);c.lineTo(730,210-thr*175);c.stroke();out.textContent=`Overall top: ${names[top]} · ${p[top].toFixed(3)}; threshold ${thr.toFixed(2)} → ${result||'no gesture'}. Bars normalised to sum 1. No event counter: smoothing, warm-up and cooldown belong to the actual detector.`;
  }
  canvas.onclick=e=>{const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)*760/r.width,y=(e.clientY-r.top)*260/r.height;if(x>=60&&x<=730&&y>=35&&y<=210){threshold.value=W09.clamp((210-y)/175,0,1);threshold.dispatchEvent(new Event('input'));}};
  presetChange();
};
W09.widgets.metrics=(root)=>{
  const {controls,out}=W09.panel(root,'Binary confusion metrics · 16 invented labelled trial scores · not measured model results');
  const threshold=W09.range(controls,'Classification threshold',0,1,.01,.7,draw);
  const trials=[[1,.95],[1,.91],[1,.84],[1,.78],[1,.72],[1,.64],[1,.49],[1,.31],[0,.88],[0,.7],[0,.6],[0,.42],[0,.25],[0,.17],[0,.09],[0,.02]];
  const table=W09.el('table'),scores=W09.el('p',{class:'trial-scores'});root.append(table,scores);
  function draw(){const m=W09.metrics(trials,+threshold.value),pct=x=>x===null?'n/a':(x*100).toFixed(1)+'%';table.replaceChildren();[['Actual / Predicted','Positive','Negative'],['Positive',`TP ${m.tp}`,`FN ${m.fn}`],['Negative',`FP ${m.fp}`,`TN ${m.tn}`]].forEach((row,i)=>{const tr=W09.el('tr');row.forEach(v=>tr.append(W09.el(i?'td':'th',{},v)));table.append(tr);});out.textContent=`Accuracy ${pct(m.accuracy)} · Precision ${pct(m.precision)} · Recall ${pct(m.recall)}`;scores.textContent='Fixed trials (actual:score): '+trials.map(([y,p])=>`${y?'P':'N'}:${p.toFixed(2)}${p>=+threshold.value?' ✓':''}`).join(' · ');}draw();
};
W09.widgets.command=(root)=>{
  const {controls,out}=W09.panel(root,'Command builder · copy into your activated terminal · commands do not execute here');
  const files=['lab9_1_time_domain.py','lab9_2_frequency.py','lab9_3_display_basics.py','lab9_4_live_charts.py','lab9_5_model_view.py'];
  const lab=W09.select(controls,'Lab',files,draw),mode=W09.select(controls,'Source',['replay bundled','replay custom file','live board'],draw);
  const seconds=W09.range(controls,'Duration (s)',1,120,1,10,draw);
  function field(label,placeholder){const l=W09.el('label',{},label),i=W09.el('input',{type:'text',placeholder,'aria-label':label});l.append(i);controls.append(l);i.oninput=draw;return i;}
  const port=field('Port (optional)','COM5'),csv=field('CSV path','imu_dataset/shake/s01_yourname_ws28p_0000.csv');
  const pre=W09.el('pre'),code=W09.el('code');pre.append(code);root.append(pre);const button=W09.el('button',{},'Copy command');button.onclick=()=>W09.copy(code.textContent,button);root.append(button);
  function draw(){const fileOnly=lab.value===files[1];if(fileOnly&&mode.value==='live board')mode.value='replay bundled';seconds.disabled=port.disabled=fileOnly;csv.disabled=mode.value!=='replay custom file';
    const valid=s=>/^[a-zA-Z0-9_./\\: -]*$/.test(s)&&!s.startsWith('-');
    const path=csv.value.trim()||csv.placeholder,p=port.value.trim();const ok=valid(path)&&(!p||valid(p));
    let cmd='python '+lab.value;if(mode.value.startsWith('replay'))cmd+=' --replay'+(mode.value==='replay custom file'?" '"+path+"'":'');if(!fileOnly)cmd+=' --seconds '+seconds.value;if(!fileOnly&&p)cmd+=" --port '"+p+"'";
    code.textContent=ok?cmd:'Use a simple path/port without shell operators or quotes.';button.disabled=!ok;out.textContent=fileOnly?'Lab 9.2 always analyses files; --seconds and --port do not affect its analysis.':(files.indexOf(lab.value)>=2?'A physical display board is required even with replay.':'Replay works without a board. Live requires ws28p.');}draw();
};
W09.widgets.pipeline=(root)=>{
  const {controls,out}=W09.panel(root,'Lab architecture · click or use Tab/Enter to inspect each processing location');
  const stages=[['MCU · sensor','QMI8658 → six SI-unit channels, nominally 50 Hz, board timestamps.'],['USB · samples','The host receives IMU frames; replay substitutes CSV rows at this boundary.'],['HOST · Python','NumPy FFT and magnitude; 100 × 6 model input; TFLite gesture inference; UI decisions.'],['USB · draw commands','Host queues shapes and text; flush batches and paces operations.'],['MCU · screen + touch','Firmware paints the screen and returns touch/page events to the host.']];
  const flow=W09.el('div',{class:'pipeline'});root.append(flow);stages.forEach(([title,body],i)=>{const b=W09.el('button',{},`${i+1}. ${title}`);b.onclick=()=>out.textContent=body;flow.append(b);});out.textContent=stages[0][1];
};
