/* Display previews approximate drawing geometry; no firmware/transport emulation. */
W09.widgets.display=(root)=>{
  const {controls,out}=W09.panel(root,'Display geometry emulator · 320 × 240 · no firmware or USB connection');
  const shape=W09.select(controls,'Operation',['fill_rect','rect','circle','line','text'],draw);
  const x=W09.range(controls,'x',0,300,1,10,draw),y=W09.range(controls,'y',46,221,1,110,draw);
  const w=W09.range(controls,'Width / radius / end x',1,300,1,120,draw),h=W09.range(controls,'Height / end y',1,221,1,30,draw);
  const color=W09.select(controls,'Colour',['GREEN','YELLOW','RED','CYAN'],draw);
  const c=W09.canvas(root,640,480,'LCD emulator with firmware regions shaded');
  const pre=W09.el('pre'),code=W09.el('code');pre.append(code);root.append(pre);
  const copy=W09.el('button',{},'Copy Python');copy.onclick=()=>W09.copy(code.textContent,copy);root.append(copy);
  function draw(){const ctx=c.getContext('2d');ctx.save();ctx.scale(2,2);ctx.fillStyle='#020811';ctx.fillRect(0,0,320,240);ctx.fillStyle='#26384c';ctx.fillRect(0,0,320,46);ctx.fillRect(0,222,320,18);ctx.font='10px monospace';ctx.fillStyle='white';ctx.fillText('HOST | METER       firmware owns y 0–45',6,20);ctx.fillText('firmware footer · y 222–239',6,234);ctx.strokeStyle='#5d6f87';ctx.strokeRect(0,46,320,176);
    const X=+x.value,Y=+y.value,W=+w.value,H=+h.value;ctx.save();ctx.beginPath();ctx.rect(0,46,320,176);ctx.clip();ctx.strokeStyle=ctx.fillStyle={GREEN:'#4ee090',YELLOW:'#ffdb69',RED:'#ff6775',CYAN:'#46d9ee'}[color.value];ctx.lineWidth=1;
    let args=`${X}, ${Y}, ${W}, ${H}`;
    if(shape.value==='fill_rect')ctx.fillRect(X,Y,W,H);
    if(shape.value==='rect')ctx.strokeRect(X,Y,W,H);
    if(shape.value==='circle'){ctx.beginPath();ctx.arc(X,Y,W,0,Math.PI*2);ctx.fill();args=`${X}, ${Y}, ${W}`;}
    if(shape.value==='line'){ctx.beginPath();ctx.moveTo(X,Y);ctx.lineTo(W,H);ctx.stroke();}
    if(shape.value==='text'){ctx.font='16px monospace';ctx.fillText('hello',X,Y+14);args=`${X}, ${Y}, "hello"`;}
    ctx.restore();ctx.restore();code.textContent=`import robotos_edge as rk\nd = rk.Display.open(name="METER")\nd.${shape.value}(${args}, rk.Color.${color.value})\nd.flush()`;
    out.textContent='Body-only clipping is imposed by this preview. Browser fonts, line rasterisation and panel gamma differ from the device.';
  }draw();
};
W09.widgets.rgb565=(root)=>{
  const {controls,out}=W09.panel(root);const r=W09.range(controls,'Red',0,255,1,255,draw),g=W09.range(controls,'Green',0,255,1,220,draw),b=W09.range(controls,'Blue',0,255,1,0,draw);
  const swatches=W09.el('div',{class:'swatches'});root.append(swatches);
  function draw(){const R=+r.value,G=+g.value,B=+b.value,v=W09.rgb565(R,G,B);out.textContent=`0x${v.toString(16).toUpperCase().padStart(4,'0')} · bits ${v.toString(2).padStart(16,'0')} · R5=${R>>3}, G6=${G>>2}, B5=${B>>3}`;swatches.replaceChildren();[[`RGB888 (${R},${G},${B})`,[R,G,B]],['RGB565 expanded preview',[Math.round((R>>3)*255/31),Math.round((G>>2)*255/63),Math.round((B>>3)*255/31)]]].forEach(([label,col])=>{const box=W09.el('div',{},label);box.style.background=`rgb(${col.join(',')})`;box.style.color=(col[0]*.3+col[1]*.6+col[2]*.1)>130?'#07162c':'#fff';swatches.append(box);});}draw();
};
W09.widgets.dirty=(root)=>{
  const {controls,out}=W09.panel(root,'Dirty rectangle simulation · pixel area is not USB payload size');
  let oldWidth=150,oldColor='GREEN';
  const width=W09.range(controls,'New bar width (px)',0,300,1,200,draw),color=W09.select(controls,'New colour',['GREEN','YELLOW','RED'],draw);
  const apply=W09.el('button',{},'Commit as previous frame');controls.append(apply);apply.onclick=()=>{oldWidth=+width.value;oldColor=color.value;draw();};
  const canvas=W09.canvas(root,760,220,'Previous bar, new bar and minimum changed regions');
  function draw(){const W=+width.value,C=color.value,d=W09.dirty(oldWidth,W,oldColor,C),ctx=canvas.getContext('2d');ctx.fillStyle='#0b1930';ctx.fillRect(0,0,760,220);ctx.font='15px system-ui';const colors={GREEN:'#50d994',YELLOW:'#ffdb69',RED:'#ff6775'};[[oldWidth,oldColor,'Previous',50],[W,C,'New',115]].forEach(([n,col,label,y])=>{ctx.fillStyle='white';ctx.fillText(label,12,y+21);ctx.strokeStyle='#c7d8ea';ctx.strokeRect(110,y,600,30);ctx.fillStyle=colors[col];ctx.fillRect(110,y,n*2,30);});ctx.fillStyle='#ffad66';const start=oldColor!==C?0:Math.min(oldWidth,W),pixels=oldColor!==C?Math.max(oldWidth,W):Math.abs(oldWidth-W);ctx.fillRect(110+start*2,170,pixels*2,12);ctx.fillStyle='white';ctx.fillText('Changed',12,182);out.textContent=`Previous ${oldWidth}px ${oldColor} → ${W}px ${C} · changed area ${d.pixels.toLocaleString()} px · bar operations ${d.operations} · whole bar area 9,000 px. Text updates are extra.`;}draw();
};
W09.widgets.bubble=(root)=>{
  const {controls,out}=W09.panel(root,'Educational level simulation · lab axis clipping and optional radial limiting');
  const ax=W09.range(controls,'ax (m/s²)',-15,15,.1,0,draw),ay=W09.range(controls,'ay (m/s²)',-15,15,.1,0,draw);
  const mode=W09.select(controls,'Position mapping',['Lab: independent axis clip','Extension: radial limit'],draw),canvas=W09.canvas(root,760,250,'Bubble position within circular dial');
  const reset=W09.el('button',{},'Return to level');controls.append(reset);reset.onclick=()=>{ax.value=ay.value=0;ax.dispatchEvent(new Event('input'));ay.dispatchEvent(new Event('input'));};
  function draw(){let dx=W09.clamp(+ax.value/9.80665,-1,1)*27,dy=W09.clamp(+ay.value/9.80665,-1,1)*27;if(mode.value.startsWith('Extension')&&Math.hypot(dx,dy)>27){const f=27/Math.hypot(dx,dy);dx*=f;dy*=f;}const c=canvas.getContext('2d');c.fillStyle='#0b1930';c.fillRect(0,0,760,250);c.save();c.translate(220,125);c.scale(2.6,2.6);c.fillStyle='#243b55';c.beginPath();c.arc(0,0,34,0,Math.PI*2);c.fill();c.strokeStyle='#7e94ac';c.beginPath();c.moveTo(-34,0);c.lineTo(34,0);c.moveTo(0,-34);c.lineTo(0,34);c.stroke();c.fillStyle='#ffdf70';c.beginPath();c.arc(Math.trunc(dx),Math.trunc(dy),7,0,Math.PI*2);c.fill();c.restore();c.fillStyle='white';c.font='19px system-ui';c.fillText(`dx=${Math.trunc(dx)} px, dy=${Math.trunc(dy)} px`,400,100);c.fillText('dial radius=34; bubble radius=7',400,140);out.textContent='Positive ay moves down in the lab’s screen mapping. Quasi-static tilt only; dynamic motion is not a reliable tilt measurement.';}draw();
};
W09.widgets.strip=(root)=>{
  const {controls,out}=W09.panel(root,'Sweep chart simulation · synthetic 50 Hz samples · timing is illustrative');
  const px=W09.range(controls,'Pixels per sample',1,4,1,1,reset),amp=W09.range(controls,'Motion amplitude (m/s²)',0,30,1,8,()=>{});
  const run=W09.el('button',{},'Pause'),step=W09.el('button',{},'Step 5 samples');controls.append(run,step);
  const canvas=W09.canvas(root,760,280,'Three-axis sweep chart; red ax, green ay, blue az');
  const c=canvas.getContext('2d');let n=0,col=0,playing=true,timer;const history=Array(312).fill(null);
  function paint(){c.fillStyle='#0b1930';c.fillRect(0,0,760,280);c.fillStyle='white';c.font='14px system-ui';c.fillText('ax red · ay green · az blue · range −20…20 m/s²',20,20);c.strokeStyle='#456079';c.strokeRect(50,40,624,180);history.forEach((row,i)=>{if(!row)return;row.forEach((v,j)=>{c.fillStyle=['#ff727a','#6ee6a1','#72a8ff'][j];const y=40+(1-W09.clamp((v+20)/40,0,1))*179;c.fillRect(50+i*2,y,2,3);});});c.fillStyle='white';c.fillRect(50+col*2,40,2,180);out.textContent=`${n} samples · cursor column ${col} · time across chart ${(312/(50*+px.value)).toFixed(2)} s · batches are 5 samples; browser timer is not a measured link rate`;
  }
  function batch(){for(let k=0;k<5;k++){const t=n++/50,A=+amp.value,row=[A*Math.sin(t*6),A*.5*Math.cos(t*4),-9.80665+A*.2*Math.sin(t*3)];for(let j=0;j<+px.value;j++){history[col]=row;col=(col+1)%312;}}paint();}
  function reset(){n=col=0;history.fill(null);paint();}
  run.onclick=()=>{playing=!playing;run.textContent=playing?'Pause':'Play';};step.onclick=batch;
  timer=setInterval(()=>{if(playing&&!document.hidden)batch();},100);reset();return ()=>clearInterval(timer);
};
