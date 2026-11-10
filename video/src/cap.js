const {chromium}=require('playwright');const fs=require('fs');const {spawn}=require('child_process');
(async()=>{
 const tl=JSON.parse(fs.readFileSync('timeline.json'));const total=Math.floor(tl.total*tl.fps);
 const only=process.argv[2]?process.argv[2].split(',').map(Number):null;
 const b=await chromium.launch({args:['--allow-file-access-from-files']});const p=await b.newPage({viewport:{width:1080,height:1920}});
 await p.goto('file://'+process.cwd()+'/render.html');await p.evaluate(tl=>init(tl),tl);
 if(only){for(const f of only){const [d]=await p.evaluate(([f])=>{for(let k=Math.max(0,f-3);k<f;k++)render(k);return batch(f,f+1,0.9)},[f]);fs.writeFileSync(`shot_${f}.jpg`,Buffer.from(d.split(',')[1],'base64'))}await b.close();return}
 const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-c:v','mjpeg','-framerate',String(tl.fps),'-i','-','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','video.mp4'],{stdio:['pipe','inherit','inherit']});
 const B=30;const t0=Date.now();
 for(let f=0;f<total;f+=B){const arr=await p.evaluate(([a,e])=>batch(a,e,0.92),[f,Math.min(total,f+B)]);
  for(const d of arr){if(!ff.stdin.write(Buffer.from(d.split(',')[1],'base64')))await new Promise(r=>ff.stdin.once('drain',r))}
  if(f%300==0)console.log(f,'/',total,((Date.now()-t0)/1000).toFixed(0)+'s')}
 ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close();console.log('done')})();
