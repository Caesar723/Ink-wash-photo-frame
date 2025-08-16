const els = {
picker: document.getElementById('ssidPicker'),
navL: document.querySelector('#pickerNavL button'),
navR: document.querySelector('#pickerNavR button'),
psk: document.getElementById('psk'),
togglePwd: document.getElementById('togglePwd'),
connectBtn: document.getElementById('connectBtn'),
busy: document.getElementById('busy'),
msg: document.getElementById('msg'),
successCard: document.getElementById('successCard'),
ip: document.getElementById('ip'),
copyIp: document.getElementById('copyIp'),
ssidHint: document.getElementById('ssidHint'),
deviceInfo: document.getElementById('deviceInfo'),
};

let ssids = [];            // 真实网络
let selected = "__auto__"; // 默认项

function setBusy(b){
els.connectBtn.disabled = b;
els.navL.disabled = b; els.navR.disabled = b;
els.busy.style.display = b ? 'inline-flex' : 'none';
els.psk.disabled = b;
[...els.picker.children].forEach(c=> c.style.pointerEvents = b ? 'none' : '');
}

function showMsg(text, type='info'){
const cls = {info:'msg-info', ok:'msg-ok', warn:'msg-warn', err:'msg-err'}[type] || 'msg-info';
els.msg.className = cls;
els.msg.textContent = text || '';
}

// 渲染极简卡片（只显示 SSID）
function renderPicker(){
els.picker.innerHTML = '';
const items = [
    // { name:'默认（自动选择，2.4G 优先）', value:'__auto__' },
    ...ssids.map(s => ({ name:s, value:s })),
];

els.ssidHint.textContent =
    items.length > 1 ? `发现 ${items.length-1} 个网络：左右滑动选择` : '未发现网络，靠近路由器或稍后重试';

items.forEach(it=>{
    const card = document.createElement('div');
    card.className = 'ssid-card' + (it.value === selected ? ' active' : '');
    card.setAttribute('role','button');
    card.setAttribute('tabindex','0');
    card.dataset.value = it.value;
    card.innerHTML = `<div class="ssid-name" title="${it.name}">${it.name}</div>`;
    card.addEventListener('click', ()=> setActive(it.value, true));
    card.addEventListener('keydown', (e)=>{ if(e.key==='Enter' || e.key===' '){ setActive(it.value, true); e.preventDefault(); }});
    els.picker.appendChild(card);
});

queueMicrotask(()=> scrollToValue(selected, {smooth:false}));
}

function setActive(value, center=false){
selected = value;
[...els.picker.children].forEach(c=> c.classList.toggle('active', c.dataset.value === value));
if(center) scrollToValue(value, {smooth:true});
}

function scrollToValue(value, {smooth=true}={}){
const card = [...els.picker.children].find(c=> c.dataset.value === value);
if(!card) return;
const box = els.picker.getBoundingClientRect();
const cb = card.getBoundingClientRect();
const offset = (cb.left + cb.width/2) - (box.left + box.width/2);
els.picker.scrollBy({ left: offset, behavior: smooth ? 'smooth' : 'auto' });
}

// 滚动后自动吸附并高亮居中卡片
let snapTimer = null;
els.picker.addEventListener('scroll', ()=>{
if(snapTimer) clearTimeout(snapTimer);
snapTimer = setTimeout(()=>{
    const centerX = els.picker.getBoundingClientRect().left + els.picker.clientWidth/2;
    let best = null, bestDist = Infinity;
    [...els.picker.children].forEach(c=>{
    const r = c.getBoundingClientRect();
    const cx = r.left + r.width/2;
    const d = Math.abs(cx - centerX);
    if(d < bestDist){ bestDist = d; best = c; }
    });
    if(best) setActive(best.dataset.value, false);
}, 90);
});

// 左右按钮
els.navL.addEventListener('click', ()=> step(-1));
els.navR.addEventListener('click', ()=> step(1));
function step(dir){
const cards = [...els.picker.children];
const idx = Math.max(0, cards.findIndex(c=> c.dataset.value===selected));
const next = cards[idx + dir] || cards[idx];
setActive(next.dataset.value, true);
}

// 拉取 SSID
async function fetchSSIDs(){
try{
    els.ssidHint.textContent = '正在扫描附近网络…';
    const r = await fetch('/api/ssids', { cache:'no-store' });
    if(!r.ok) throw new Error('HTTP '+r.status);
    const data = await r.json();
    const list = Array.isArray(data.ssids) ? data.ssids : [];

    ssids = list;
    renderPicker();
    showMsg('已更新 Wi-Fi 列表','ok');
}catch(e){
    showMsg('获取 Wi-Fi 列表失败：' + e.message, 'err');
    ssids = [];
    renderPicker();
}
}

async function postConnect(ssid, psk){
const form = new URLSearchParams({ ssid, psk });
const r = await fetch('/api/connect', {
    method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'},
    body: form.toString(),
});
return r.ok;
}

async function pollStatus(timeoutSec=25){
const t0 = Date.now();
while(Date.now()-t0 < timeoutSec*1000){
    try{
    const r = await fetch('/api/status?ts='+Date.now(), { cache:'no-store' });
    if(r.ok){
        const d = await r.json();
        if(d.connected && d.ip){
        els.ip.textContent = d.ip;
        els.successCard.classList.add('show');
        els.successCard.style.display = 'block';
        showMsg('连接成功','ok');
        return true;
        }
    }
    }catch(_){}
    await new Promise(res=>setTimeout(res, 1000));
}
return false;
}

async function handleConnect(){
const ssid = (selected || '').trim();
const psk  = els.psk.value;
if(!ssid){ showMsg('请选择一个 Wi-Fi','warn'); return; }
if(ssid !== '__auto__' && !psk){
    showMsg('该网络可能需要密码，请填写或确认是开放网络','warn');
}

els.successCard.classList.remove('show');
els.successCard.style.display='none';
showMsg('');
setBusy(true);
try{
    const ok = await postConnect(ssid, psk);
    if(!ok) throw new Error('提交失败');
    showMsg('已提交，正在连接…','info');
    const done = await pollStatus(25);
    if(!done) showMsg('暂未获取到 IP，请稍后重试或刷新列表','warn');
}catch(e){
    showMsg('连接出错：' + e.message, 'err');
}finally{
    setBusy(false);
}
}

// 事件
els.connectBtn.addEventListener('click', handleConnect);
document.addEventListener('keydown', (e)=>{
if(e.key === 'Enter'){
    const tag = (document.activeElement?.tagName || '').toLowerCase();
    if(tag === 'input' || tag === 'button' || tag === 'div') handleConnect();
}else if(e.key === 'ArrowLeft'){ step(-1) }
else if(e.key === 'ArrowRight'){ step(1) }
});

// 显示/隐藏密码
els.togglePwd.addEventListener('click', () => {
const hidden = els.psk.type === 'password';
els.psk.type = hidden ? 'text' : 'password';
els.togglePwd.textContent = hidden ? '隐藏' : '显示';
els.togglePwd.setAttribute('aria-pressed', hidden ? 'true' : 'false');
els.psk.focus({ preventScroll:true });
});

// 复制 IP
els.copyIp?.addEventListener('click', async ()=>{
const ip = els.ip.textContent.trim();
if(!ip) return;
try{
    await navigator.clipboard.writeText(ip);
    showMsg('已复制 IP：' + ip, 'ok');
}catch{
    showMsg('复制失败，请手动选择复制', 'warn');
}
});

// 初始化
(async ()=>{
els.deviceInfo.textContent = '设备就绪：请连接 Wi-Fi';
renderPicker();      // 先渲染默认项
await fetchSSIDs();  // 拉真实数据
})();





async function copyText(text) {
    // 1) 现代剪贴板 API（仅 HTTPS/localhost 可用）
    if (window.isSecureContext && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      await navigator.clipboard.writeText(text);
      return true;
    }
    // 2) 回退：textarea + execCommand('copy')（HTTP 也可用）
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.top = '-1000px';
      document.body.appendChild(ta);

      ta.focus();
      ta.select();
      ta.setSelectionRange(0, ta.value.length); // 兼容 iOS

      const ok = document.execCommand('copy');   // 已弃用但仍广泛可用
      document.body.removeChild(ta);
      return ok;
    } catch (e) {
      return false;
    }
  }


async function initCopyBtn(){

    const response=await fetch("/api/get_hostname")
    const data=await response.json()
    const hostname=data.hostname
    const port=data.port
    document.getElementById("localLink").textContent = `http://${hostname}.local:${port}`;
}

initCopyBtn()
document.getElementById("copyBtn").addEventListener("click", async () => {
    try {
        const link=document.getElementById("localLink").textContent;
        const ok = await copyText(link);
        document.getElementById("copyHint").textContent = ok ? `已复制：${link}` : "复制失败，请手动选择复制";
    } catch (err) {
        document.getElementById("copyHint").textContent = "复制失败，请手动复制";
        console.error("复制失败：", err);
    }
});