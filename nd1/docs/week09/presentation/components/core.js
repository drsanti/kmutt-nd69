/* Reusable numerical and DOM helpers. No dependencies or network access. */
globalThis.W09 = globalThis.W09 || {};
Object.assign(W09, {
  widgets: {},
  clamp: (v, lo, hi) => Math.max(lo, Math.min(hi, v)),
  alias: (f, fs) => Math.abs(((f + fs / 2) % fs + fs) % fs - fs / 2),
  rgb565: (r,g,b) => ((r & 248) << 8) | ((g & 252) << 3) | (b >> 3),
  normalise: row => row.map((x,i) => W09.clamp(x/(i<3?9.80665:4),-4,4)),
  spectrum(x, fs=50, removeMean=true) {
    const n=x.length, mean=removeMean?x.reduce((a,b)=>a+b,0)/n:0;
    return Array.from({length:Math.floor(n/2)+1},(_,k)=>{
      let re=0,im=0;
      for(let j=0;j<n;j++){const a=2*Math.PI*k*j/n; re+=(x[j]-mean)*Math.cos(a); im-=(x[j]-mean)*Math.sin(a);}
      return [k*fs/n,Math.hypot(re,im)];
    });
  },
  decision(p, threshold) {
    const top=p.indexOf(Math.max(...p));
    return top!==0 && p[top]>=threshold?['idle','shake','circle','lift'][top]:null;
  },
  metrics(trials, threshold) {
    const m={tp:0,fp:0,tn:0,fn:0};
    trials.forEach(([truth,score])=>m[truth?(score>=threshold?'tp':'fn'):(score>=threshold?'fp':'tn')]++);
    const ratio=(a,b)=>b?a/b:null;
    return {...m,accuracy:ratio(m.tp+m.tn,trials.length),precision:ratio(m.tp,m.tp+m.fp),recall:ratio(m.tp,m.tp+m.fn)};
  },
  dirty(oldWidth,width,oldColor,color,height=30) {
    return {pixels:(oldColor!==color?Math.max(oldWidth,width):Math.abs(width-oldWidth))*height,
      operations:oldColor!==color?Number(width>0)+Number(width<oldWidth):Number(width!==oldWidth)};
  },
  el(tag,attrs={},text='') {
    const n=document.createElement(tag); Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v)); n.textContent=text; return n;
  },
  panel(root,label='Educational simulation · JavaScript, no hardware connection') {
    root.append(W09.el('p',{class:'provenance'},label));
    const controls=W09.el('div',{class:'controls'}), out=W09.el('output',{'aria-live':'polite',class:'readout'});
    root.append(controls,out); return {controls,out};
  },
  range(root,label,min,max,step,value,update) {
    const wrap=W09.el('label',{},label+' '), output=W09.el('span',{},String(value));
    const input=W09.el('input',{type:'range',min,max,step,value,'aria-label':label});
    wrap.append(output,input); root.append(wrap);
    input.addEventListener('input',()=>{output.textContent=input.value;update();}); return input;
  },
  select(root,label,options,update) {
    const wrap=W09.el('label',{},label+' '), input=W09.el('select',{'aria-label':label});
    options.forEach(o=>input.append(W09.el('option',{value:o},o))); wrap.append(input);root.append(wrap);
    input.addEventListener('change',update);return input;
  },
  canvas(root,w=760,h=260,label='Interactive plot') {
    const c=W09.el('canvas',{width:w,height:h,role:'img','aria-label':label});root.append(c);return c;
  },
  plot(canvas,series,{xmin=0,xmax=2,ymin=-2,ymax=2,xlabel='time (s)',ylabel='value',dots=false}={}) {
    const c=canvas.getContext('2d'),w=canvas.width,h=canvas.height,l=58,r=18,t=25,b=38;
    c.fillStyle='#0b1930';c.fillRect(0,0,w,h);c.font='13px system-ui';
    const px=x=>l+(x-xmin)/(xmax-xmin)*(w-l-r),py=y=>h-b-(y-ymin)/(ymax-ymin)*(h-t-b);
    c.strokeStyle='#334563';c.fillStyle='#c7d8ea';
    for(let i=0;i<=4;i++){let y=ymin+(ymax-ymin)*i/4;c.beginPath();c.moveTo(l,py(y));c.lineTo(w-r,py(y));c.stroke();c.fillText(y.toFixed(1),4,py(y)+4);let x=xmin+(xmax-xmin)*i/4;c.fillText(x.toFixed(1),px(x)-10,h-18);}
    c.fillText(ylabel,l,16); c.fillText(xlabel,w-100,h-3);
    series.forEach((s,i)=>{c.strokeStyle=s.color||['#47dbf3','#ffb65a','#77eeaf'][i%3];c.fillStyle=c.strokeStyle;c.lineWidth=2;c.beginPath();s.data.forEach(([x,y],j)=>{if(!j)c.moveTo(px(x),py(y));else c.lineTo(px(x),py(y));});c.stroke();if(dots||s.dots)s.data.forEach(([x,y])=>{c.beginPath();c.arc(px(x),py(y),3,0,Math.PI*2);c.fill();});});
  },
  async copy(text,button) {
    try {await navigator.clipboard.writeText(text);button.textContent='Copied';}
    catch {const area=W09.el('textarea',{'aria-label':'Select and copy code'});area.value=text;button.after(area);area.select();button.textContent='Select text and copy';}
  }
});
