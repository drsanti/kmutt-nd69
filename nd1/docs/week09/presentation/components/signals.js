/* Signal generator, sampling, aliasing, numerical DFT, repository CSV explorer. */
W09.widgets.signal = W09.widgets.sampling = W09.widgets.aliasing = W09.widgets.fft = (root,kind) => {
  const {controls,out}=W09.panel(root), isAlias=kind==='aliasing';
  const a=W09.range(controls,'Amplitude',0,3,.1,1,draw),f=W09.range(controls,'Frequency (Hz)',1,isAlias?60:20,.25,isAlias?40:5,draw);
  const fs=W09.range(controls,'Sample rate (Hz)',10,150,5,50,draw),phase=W09.range(controls,'Phase (degrees)',0,360,15,0,draw);
  const dc=W09.range(controls,'DC offset',0,10,.5,0,draw),mix=W09.range(controls,'15 Hz amplitude',0,1,.1,0.4,draw);
  const duration=W09.range(controls,'Window (s)',1,4,1,2,draw);
  const mean=W09.select(controls,'Mean removal',['on','off'],draw);
  if(kind!=='fft')mean.parentElement.hidden=true;
  if(isAlias)mix.parentElement.hidden=true;
  const wave=W09.canvas(root,760,235,'Signal and acquired samples; cyan continuous, orange samples');
  const spec=kind==='fft'?W09.canvas(root,760,220,'Computed DFT magnitude versus frequency'):null;
  function draw(){
    const A=+a.value,F=+f.value,FS=+fs.value,T=+duration.value,P=+phase.value*Math.PI/180,D=+dc.value,M=+mix.value;
    const fn=t=>A*Math.sin(2*Math.PI*F*t+P)+D+(isAlias?0:M*Math.sin(2*Math.PI*15*t));
    const samples=Array.from({length:Math.round(FS*T)},(_,i)=>[i/FS,fn(i/FS)]);
    const dense=Array.from({length:1201},(_,i)=>[i*T/1200,fn(i*T/1200)]);
    const extent=Math.max(1,A+M+.3);
    const series=[{data:dense}];
    if(isAlias){const signed=((F+FS/2)%FS+FS)%FS-FS/2;series.push({data:dense.map(([t])=>[t,D+A*Math.sin(2*Math.PI*signed*t+P)]),color:'#77eeaf'});}
    series.push({data:samples,dots:true,color:'#ffb65a'});
    W09.plot(wave,series,{xmax:T,ymin:D-extent,ymax:D+extent,ylabel:isAlias?'cyan original · green alias · orange samples':'amplitude'});
    const alias=W09.alias(F,FS);
    out.textContent=`N=${samples.length} · Ts=${(1000/FS).toFixed(2)} ms · Nyquist=${FS/2} Hz · Δf=${(1/T).toFixed(3)} Hz${isAlias?' · apparent f='+alias.toFixed(2)+' Hz':''}`;
    if(spec){const bins=W09.spectrum(samples.map(p=>p[1]),FS,mean.value==='on');W09.plot(spec,[{data:bins}],{xmax:FS/2,ymin:0,ymax:Math.max(1,...bins.map(p=>p[1]))*1.1,xlabel:'frequency (Hz)',ylabel:'raw |DFT|'});}
  }
  draw();
};
W09.widgets.dataset=W09.widgets['dataset-fft']=W09.widgets.tensor=(root,kind)=>{
  const {controls,out}=W09.panel(root,'Repository data · exact bundled CSV values · synthetic, not measured IMU data');
  const file=W09.select(controls,'Gesture',Object.keys(W09_DATA),draw),view=W09.select(controls,'Channels',['acceleration','gyroscope','magnitude'],draw);
  const plot=W09.canvas(root,760,245,'Repository time series; x red, y green, z blue');
  const extra=kind==='dataset-fft'||kind==='tensor'?W09.canvas(root,760,220,kind==='tensor'?'Normalised 100 by 6 model input':'FFT of repository acceleration magnitude'):null;
  function draw(){const rows=W09_DATA[file.value],mag=rows.map(r=>Math.hypot(...r.slice(1,4)));let series,ymin,ymax;
    if(view.value==='magnitude'){series=[{data:rows.map((r,i)=>[r[0],mag[i]])}];ymin=0;ymax=25;}
    else{const offset=view.value==='acceleration'?1:4;series=[0,1,2].map((j)=>({data:rows.map(r=>[r[0],r[offset+j]]),color:['#ff727a','#6ee6a1','#72a8ff'][j]}));ymin=offset===1?-20:-5;ymax=offset===1?20:5;}
    W09.plot(plot,series,{xmax:2,ymin,ymax,ylabel:view.value==='gyroscope'?'rad/s':'m/s²'});
    const bins=W09.spectrum(mag),peak=bins.slice(1).reduce((a,b)=>b[1]>a[1]?b:a);
    out.textContent=`${file.value}.csv · ${rows.length} rows · t=0…${rows.at(-1)[0]} s · |a| peak bin=${peak[0].toFixed(2)} Hz (not necessarily the motion fundamental)`;
    if(extra&&kind==='dataset-fft')W09.plot(extra,[{data:bins}],{xmax:25,ymin:0,ymax:Math.max(...bins.map(x=>x[1]))*1.1,xlabel:'frequency (Hz)',ylabel:'raw |FFT|'});
    if(extra&&kind==='tensor'){const c=extra.getContext('2d');c.fillStyle='#0b1930';c.fillRect(0,0,760,220);const names=['ax','ay','az','gx','gy','gz'];rows.forEach((r,x)=>W09.normalise(r.slice(1)).forEach((v,y)=>{const f=W09.clamp((v+2)/4,0,1);c.fillStyle=`rgb(${Math.round(240*f)},${Math.round(70+150*f)},${Math.round(200-140*f)})`;c.fillRect(52+x*7,y*30+18,7,29);}));c.font='13px system-ui';c.fillStyle='white';names.forEach((n,y)=>c.fillText(n,10,y*30+38));c.fillText('0                       sample index → 99 · display colour range −2…2',52,214);}
  }draw();
};
W09.widgets.imu=(root)=>{
  const {controls,out}=W09.panel(root,'Educational IMU simulation · one-axis tilt with added vertical acceleration');
  const angle=W09.range(controls,'Tilt (degrees)',-90,90,1,0,draw),acc=W09.range(controls,'Added z acceleration (m/s²)',-10,10,.1,0,draw);
  const canvas=W09.canvas(root,760,240,'Gravity components and magnitude');
  function draw(){const r=+angle.value*Math.PI/180,x=9.80665*Math.sin(r),z=-9.80665*Math.cos(r)+ +acc.value,c=canvas.getContext('2d');c.fillStyle='#0b1930';c.fillRect(0,0,760,240);c.save();c.translate(170,120);c.rotate(r);c.fillStyle='#47dbf3';c.fillRect(-85,-12,170,24);c.restore();c.font='22px system-ui';c.fillStyle='#e1ecfa';c.fillText(`ax = ${x.toFixed(2)} m/s²`,340,80);c.fillText(`az = ${z.toFixed(2)} m/s²`,340,120);c.fillText(`|a| = ${Math.hypot(x,z).toFixed(2)} m/s²`,340,160);out.textContent='Gyro is not derived from the slider speed. Static tilt alone redistributes gravity; added acceleration changes the resultant.';
  }draw();
};
