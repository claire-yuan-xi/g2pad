const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
for (const v of process.argv.slice(2)){ const [view,w,h]=v.split(':');
 const p=await b.newPage({viewport:{width:+w,height:+h}});
 p.on('console',m=>console.log(m.text())); p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto(`http://localhost:8765/index.html?view=${view}&w=${w}&h=${h}`); await p.waitForFunction(()=>document.title==='done',null,{timeout:120000});
 await p.screenshot({path:`${view}.png`}); console.log('shot',view);}
await b.close();})();
