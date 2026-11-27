/* npm ci && npx playwright install chromium && npm run test:browser
   W09_BROWSER_CHANNEL=chrome can use an existing Chrome instead. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..'),qa=process.env.W09_QA_DIR||path.join(os.tmpdir(),'nd01-week09-qa');fs.mkdirSync(qa,{recursive:true});
(async()=>{
  const browser=await chromium.launch({headless:true,...(process.env.W09_BROWSER_CHANNEL?{channel:process.env.W09_BROWSER_CHANNEL}:{})});
  const context=await browser.newContext({viewport:{width:1440,height:1000},offline:true});
  const page=await context.newPage(),errors=[],network=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url());});
  const offline=pathToFileURL(path.join(root,'dist/week09-presentation.html')).href;
  async function slide(n){await page.evaluate(n=>location.hash='#slide-'+n,n);await page.waitForFunction(n=>document.getElementById('counter').textContent===`${n} / 85`,n);}
  await page.goto(offline);await page.waitForSelector('#slide-title');
  const representative=[1,3,12,16,23,30,36,39,42,46,49,58,63,70,74,77,84];
  for(let n=1;n<=85;n++){
    await slide(n);assert.ok((await page.locator('#slide-title').textContent()).length>0);
    assert.ok(await page.locator('#notes-text').textContent());
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`desktop overflow on ${n}`);
    if(representative.includes(n))await page.screenshot({path:path.join(qa,`desktop-${n}.png`),fullPage:true});
    // Exercise every widget's numeric boundaries and every select option.
    for(const control of await page.locator('.demo input[type=range]:visible').all()){
      for(const boundary of ['min','max'])await control.evaluate((e,b)=>{e.value=e[b];e.dispatchEvent(new Event('input',{bubbles:true}));},boundary);
    }
    for(const select of await page.locator('.demo select:visible').all()){
      const values=await select.locator('option').evaluateAll(opts=>opts.map(o=>o.value));
      for(const v of values)await select.selectOption(v);
    }
    const quiz=page.locator('.quiz button');if(await quiz.count()){await quiz.first().click();assert.ok((await page.locator('.feedback').textContent()).length>5);}
    assert.equal(errors.length,0,`slide ${n}: ${errors.join('; ')}`);
  }
  await slide(20); // sampling
  const rate=page.getByRole('slider',{name:'Sample rate (Hz)'});await rate.fill('100');assert.match(await page.locator('.readout').textContent(),/Ts=10.00 ms/);
  await slide(36); // aliasing
  await page.getByRole('slider',{name:'Frequency (Hz)'}).fill('40');await page.getByRole('slider',{name:'Sample rate (Hz)'}).fill('50');assert.match(await page.locator('.readout').textContent(),/apparent f=10.00 Hz/);
  await slide(74); // decision rule
  await page.getByLabel('Preset',{exact:true}).selectOption('ambiguous');await page.getByRole('slider',{name:'Detection threshold',exact:true}).fill('.25');assert.match(await page.locator('.readout').textContent(),/no gesture/);
  const graph=page.locator('canvas');await graph.click({position:{x:100,y:100}});assert.ok(Number(await page.getByRole('slider',{name:'Detection threshold',exact:true}).inputValue())!==.25);
  await slide(12); // command builder
  await page.getByLabel('Lab',{exact:true}).selectOption('lab9_2_frequency.py');assert.ok(await page.getByRole('slider',{name:'Duration (s)'}).isDisabled());
  await page.getByLabel('Source',{exact:true}).selectOption('replay custom file');await page.getByLabel('CSV path',{exact:true}).fill('take.csv; bad');assert.ok(await page.getByRole('button',{name:'Copy command',exact:true}).isDisabled());
  await page.getByLabel('CSV path',{exact:true}).fill('samples/shake.csv');assert.match(await page.locator('.demo code').textContent(),/--replay 'samples\/shake.csv'/);
  await slide(7);await page.getByRole('button',{name:'Copy code',exact:true}).click();await page.waitForFunction(()=>['Copied','Select text and copy'].includes(document.querySelector('.copy').textContent));
  // Keyboard navigation must yield arrow keys to focused sliders.
  await page.locator('#slide-title').click();await page.keyboard.press('Home');await page.waitForFunction(()=>document.querySelector('#counter').textContent==='1 / 85');await page.keyboard.press('ArrowRight');await page.waitForFunction(()=>document.querySelector('#counter').textContent==='2 / 85');
  await page.keyboard.press('End');await page.waitForFunction(()=>document.querySelector('#counter').textContent==='85 / 85');await page.keyboard.press('n');assert.ok(await page.locator('#notes').getAttribute('open')!==null);
  await slide(1);const slider=page.getByRole('slider',{name:'Amplitude',exact:true});await slider.focus();await page.keyboard.press('ArrowRight');assert.equal(await page.locator('#counter').textContent(),'1 / 85');
  await page.getByRole('button',{name:'All slides',exact:true}).click();assert.equal(await page.locator('#overview-grid button').count(),85);await page.locator('#overview-grid button').nth(40).click();await page.waitForFunction(()=>document.querySelector('#counter').textContent==='41 / 85');
  await page.getByLabel('Jump to chapter').selectOption('7');await page.waitForFunction(()=>document.querySelector('#counter').textContent==='82 / 85');
  await page.getByRole('button',{name:'Fullscreen',exact:true}).click();await page.waitForFunction(()=>Boolean(document.fullscreenElement));await page.evaluate(()=>document.exitFullscreen());
  await page.getByRole('button',{name:'Theme',exact:true}).click();assert.ok(await page.locator('body').evaluate(e=>e.classList.contains('dark')));await page.screenshot({path:path.join(qa,'dark.png'),fullPage:true});await page.getByRole('button',{name:'Theme',exact:true}).click();
  // Prepare static print reference without opening a modal print dialog.
  await page.evaluate(()=>window.dispatchEvent(new Event('beforeprint')));assert.equal(await page.locator('.print-slide').count(),85);
  await page.emulateMedia({media:'print'});await page.screenshot({path:path.join(qa,'print.png')});await page.emulateMedia({media:'screen'});
  await page.setViewportSize({width:390,height:844});
  for(let n=1;n<=85;n++){await slide(n);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`mobile overflow ${n}`);if([1,12,42,74,77].includes(n))await page.screenshot({path:path.join(qa,`mobile-${n}.png`),fullPage:true});}
  // Also check the modular file:// entry point independently.
  await page.goto(pathToFileURL(path.join(root,'index.html')).href);await page.waitForSelector('#slide-title');for(const n of [3,12,23,30,42,49,58,63,70,74,77,85])await slide(n);
  assert.deepEqual(errors,[]);assert.deepEqual(network,[]);
  const result={slides:85,desktop:'1440×1000',mobile:'390×844',offlineFile:true,modularFile:true,errors,networkRequests:network.length,screenshots:qa,browser:browser.version()};fs.writeFileSync(path.join(qa,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
