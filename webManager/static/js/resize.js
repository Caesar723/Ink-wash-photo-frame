const box = document.getElementById('box');
const chip = document.getElementById('sizeChip');
const resetBtn = document.getElementById('resetBtn');
const snapBtn  = document.getElementById('snapBtn');
const setBtn  = document.getElementById('setBtn');
const stage = document.getElementById('stage');
const BASE_W = 480;
const BASE_H = 800;

// 初始位移（通过 transform 管理）
function scaleOfStage(){
    
    // 舞台宽=90%视口，且锁定 480:800 比例 ⇒ x/y 同比缩放
    console.log(stage.clientWidth,stage.clientHeight);
    const s = stage.clientWidth / BASE_W; // 与高度比 BASE_H 一致
    console.log(s);
    
    return s;
}

box.setAttribute('data-x', 40*scaleOfStage());
box.setAttribute('data-y', 40*scaleOfStage());

// 工具：更新尺寸标签
function updateChip(w, h){
    chip.textContent = Math.round(w) + '×' + Math.round(h);
}

async function getSize(){
    
    const res=await fetch('/api/get_size', {
        method: 'POST',
    });
    document.getElementById("advance_setting").style.display="block";
    if(res.ok){
        const data=await res.json();
        const scale = scaleOfStage();


        


        box.style.width = data.height*scale+'px';
        box.style.height = data.weight*scale+'px';
        updateChip(data.height, data.weight);

        const max_height=480;
        const max_weight=800;
        const x = data.offset_h;
        const y = max_weight-data.weight-data.offset_w;
        console.log(x,y);

        

        box.style.transform = `translate(${x*scale}px, ${y*scale}px)`;
        box.setAttribute('data-x', x);
        box.setAttribute('data-y', y);
    }
    else{
        const scale = scaleOfStage();
        const newW = parseFloat(box.clientWidth/scale);
        const newH = parseFloat(box.clientHeight/scale);
        updateChip(newW, newH);
    }
    document.getElementById("advance_setting").style.display="none";
}
getSize();

// 可拖拽
const dragModifiers = [
    // 限制拖拽不出父容器
    interact.modifiers.restrict({
    
    restriction: 'parent',


    elementRect: { left: 0, right: 1, top: 0, bottom: 1 },
    relativePoints:[{ x: 0.5, y: 0.5 }],
    
    }),
    
];

interact('#box').draggable({
    inertia: false,
    modifiers: dragModifiers,
    listeners: {
    move (event) {
        const target = event.target;
        const scale = scaleOfStage();
        let x = (parseFloat(target.getAttribute('data-x'))*scale || 0) + event.dx;
        let y = (parseFloat(target.getAttribute('data-y'))*scale || 0) + event.dy;

        console.log(x,y);
        console.log(event.rect.width,event.rect.height);
        if (x < 0) x = 0;
        if (y < 0) y = 0;
        if (x+event.rect.width > stage.clientWidth) x = parseFloat(stage.clientWidth-event.rect.width);
        if (y+event.rect.height > scaleOfStage()*BASE_H) y = parseFloat(scaleOfStage()*BASE_H-event.rect.height);
        console.log(x,y);
        console.log("end")


        target.style.transform = `translate(${x}px, ${y}px)`;
        target.setAttribute('data-x', x/scale);
        target.setAttribute('data-y', y/scale);
    }
    }
});

// 对齐网格开关（8px）
const gridSnap = interact.modifiers.snap({
    targets: [ interact.snappers.grid({ x: 8, y: 8 }) ],
    range: Infinity,
    relativePoints: [{ x: 0, y: 0 }],
});

let snapOn = false;

function currentResizeModifiers(){
    document.getElementById("advance_setting").style.display="block";
    console.log(stage.clientWidth,stage.clientHeight)
    const mods = [
    // 保证不出父容器（边缘受限）
    interact.modifiers.restrictEdges({ outer: 'parent' }),
    // 最小尺寸
    interact.modifiers.restrictSize({ min: { width: 80, height: 60 }, max: { width: stage.clientWidth, height: scaleOfStage()*BASE_H } }),
    ];
    if (snapOn) {
    // 尺寸对齐网格
    mods.push(interact.modifiers.snapSize({
        targets: [ interact.snappers.grid({ x: 8, y: 8 }) ]
    }));
    }
    document.getElementById("advance_setting").style.display="none";
    return mods;
}

// 可缩放
async function setupResizable(){
    
    
    
    interact('#box').resizable({
    edges: {
        // 让边和角的手柄都能触发缩放
        left:   '.w, .nw, .sw',
        right:  '.e, .ne, .se',
        top:    '.n, .nw, .ne',
        bottom: '.s, .sw, .se',
    },
    inertia: true,
    modifiers: currentResizeModifiers(),
    listeners: {
        move (event) {
        const target = event.target;

        const scale = scaleOfStage();
        let x = parseFloat(target.getAttribute('data-x'))*scale || 0;
        let y = parseFloat(target.getAttribute('data-y'))*scale || 0;

        

        // 更新宽高
        target.style.width  = event.rect.width + 'px';
        target.style.height = event.rect.height + 'px';
        updateChip(parseFloat(event.rect.width/scale), parseFloat(event.rect.height/scale));

        // 从上/左缩放时需要补偿位移
        x += event.deltaRect.left;
        y += event.deltaRect.top;

        if (x < 0) x = 0;
        if (y < 0) y = 0;
        if (x+event.rect.width > stage.clientWidth) x = parseFloat(stage.clientWidth-event.rect.width);
        if (y+event.rect.height > scaleOfStage()*BASE_H) y = parseFloat(scaleOfStage()*BASE_H-event.rect.height);
        console.log(x,y);
        console.log("end")

        target.style.transform = `translate(${x}px, ${y}px)`;
        target.setAttribute('data-x', x/scale);
        target.setAttribute('data-y', y/scale);
        }
    }
    });
}
setupResizable();

// —— 按钮事件 ——
resetBtn.addEventListener('click', () => {
    // 尺寸与位置复位
    const scale = scaleOfStage();
    box.style.width = parseInt(320*scale)+'px';
    box.style.height = parseInt(180*scale)+'px';
    updateChip(320, 180);

    const x = 40, y = 40;
    box.style.transform = `translate(${x}px, ${y}px)`;
    box.setAttribute('data-x', x/scale);
    box.setAttribute('data-y', y/scale);
});


function clip_value(value,min,max){
    return Math.max(min,Math.min(value,max));
}

setBtn.addEventListener('click', async () => {
    const scale = scaleOfStage();
    const width = parseFloat(box.clientWidth/scale);
    const height = parseFloat(box.clientHeight/scale);
    const offset_x = parseFloat(box.getAttribute('data-x'))+1;
    const offset_y = parseFloat(box.getAttribute('data-y'))+1;
    console.log(width, height,offset_x,offset_y);

    const max_height=480
    const max_width=800

    const conf_width = clip_value(Math.round(width),80,max_height);
    const conf_height = clip_value(Math.round(height),80,max_width);
    const config = {
        height: conf_width,
        weight: conf_height,
        offset_h: clip_value(Math.round(offset_x),0,max_height-conf_width),
        offset_w: clip_value(Math.round(max_width-conf_height-offset_y),0,max_width-conf_height)
    };

    console.log(config);
    

    const res=await fetch('/api/set_size', {
        method: 'POST',
        body: JSON.stringify(config),
    });
    if(res.ok){
        alert('设置成功');
    }else{
        alert('failed');
    }
    
});

// snapBtn.addEventListener('click', () => {
//     snapOn = !snapOn;
//     snapBtn.setAttribute('aria-pressed', String(snapOn));
    

//     // 重新应用 resizable（带新 modifiers）
//     interact('#box').unset();  // 清理旧的交互（只对这个元素）
//     // 重新绑定拖拽和缩放
//     interact('#box').draggable({ inertia:true, modifiers: dragModifiers, listeners: { move: interact.getInteractable('#box').options.drag.listeners.move } });
//     setupResizable();
// });