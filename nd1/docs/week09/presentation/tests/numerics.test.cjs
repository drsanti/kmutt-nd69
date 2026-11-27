const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
vm.runInThisContext(fs.readFileSync(path.join(__dirname,'../components/core.js'),'utf8'));
const near=(a,b,eps=1e-8)=>assert.ok(Math.abs(a-b)<eps,`${a} != ${b}`);
test('DFT matches analytic sinusoid, real bins and DC removal',()=>{
  const x=Array.from({length:100},(_,i)=>3+2*Math.sin(2*Math.PI*5*i/50));
  const spectrum=W09.spectrum(x);
  assert.equal(spectrum.length,51);near(spectrum.at(-1)[0],25);near(spectrum[10][1],100);near(spectrum[0][1],0);
  near(W09.spectrum(x,50,false)[0][1],300);
  assert.equal(spectrum.slice(1).reduce((a,b)=>a[1]>b[1]?a:b)[0],5);
});
test('alias folds across several sampling intervals and negative frequencies',()=>{
  near(W09.alias(40,50),10);near(W09.alias(60,50),10);near(W09.alias(125,50),25);near(W09.alias(-40,50),10);
  // Signed folded curve must meet original at all sample times, including phase.
  for(const f of [10,40,60,110])for(let i=0;i<100;i++){
    const signed=((f+25)%50+50)%50-25;
    near(Math.sin(2*Math.PI*f*i/50+.7),Math.sin(2*Math.PI*signed*i/50+.7));
  }
});
test('RGB565 matches SDK masks',()=>{assert.equal(W09.rgb565(255,220,0),0xFEE0);assert.equal(W09.rgb565(255,255,255),65535);assert.equal(W09.rgb565(0,0,0),0);});
test('normalisation preserves gravity and clips per channel',()=>{const a=W09.normalise([9.80665,-98.0665,0,4,40,-40]);assert.deepEqual(a,[1,-4,0,1,4,-4]);});
test('idle wins overall; threshold equality accepted; tie uses first class',()=>{
  assert.equal(W09.decision([.55,.3,.1,.05],.25),null);assert.equal(W09.decision([.1,.7,.1,.1],.7),'shake');assert.equal(W09.decision([.1,.7,.1,.1],.71),null);assert.equal(W09.decision([.5,.5,0,0],.5),null);
});
test('confusion counts and undefined denominators',()=>{const m=W09.metrics([[1,.9],[1,.4],[0,.8],[0,.1]],.7);assert.deepEqual(m,{tp:1,fp:1,tn:1,fn:1,accuracy:.5,precision:.5,recall:.5});assert.equal(W09.metrics([[1,.1]],1).precision,null);});
test('dirty area covers growth, shrink and colour repaint',()=>{
  assert.deepEqual(W09.dirty(200,150,'GREEN','GREEN'),{pixels:1500,operations:1});assert.deepEqual(W09.dirty(150,200,'GREEN','GREEN'),{pixels:1500,operations:1});assert.deepEqual(W09.dirty(200,150,'GREEN','RED'),{pixels:6000,operations:2});assert.deepEqual(W09.dirty(150,150,'GREEN','GREEN'),{pixels:0,operations:0});
});
test('all 85 slides have notes and all four CSVs are embedded exactly',()=>{
  const root=path.join(__dirname,'..'),chapters=fs.readdirSync(path.join(root,'slides')).filter(x=>x.endsWith('.json')).sort().map(x=>JSON.parse(fs.readFileSync(path.join(root,'slides',x))));
  assert.deepEqual(chapters.map(c=>c.slides.length),[5,10,12,14,13,12,15,4]);chapters.flatMap(c=>c.slides).forEach(s=>{assert.ok(s.notes);assert.ok(s.lead);s.points.forEach(p=>assert.ok(p.trim().length>2,`Malformed bullet: ${s.title}`));});
  const context=vm.createContext({});vm.runInContext(fs.readFileSync(path.join(root,'assets/content.js'),'utf8')+';globalThis.data=W09_DATA;',context);
  for(const name of ['idle','shake','circle','lift']){const csv=fs.readFileSync(path.join(root,'../labs/python/samples',name+'.csv'),'utf8').trim().split(/\r?\n/).slice(1).map(row=>row.split(',').map(Number));assert.equal(context.data[name].length,csv.length);csv.forEach((row,i)=>row.forEach((v,j)=>assert.ok(context.data[name][i][j]===v,`${name} row ${i} column ${j}`)));}
});
