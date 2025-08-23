const box = document.getElementById('box');
const chip = document.getElementById('sizeChip');
const resetBtn = document.getElementById('resetBtn');
const snapBtn  = document.getElementById('snapBtn');
const setBtn  = document.getElementById('setBtn');

// 初始位移（通过 transform 管理）
box.setAttribute('data-x', 40);
box.setAttribute('data-y', 40);

// 工具：更新尺寸标签
function updateChip(w, h){
    chip.textContent = Math.round(w) + '×' + Math.round(h);
}
updateChip(box.clientWidth, box.clientHeight);

// 可拖拽
const dragModifiers = [
    // 限制拖拽不出父容器
    interact.modifiers.restrict({
    restriction: 'parent',
    elementRect: { left: 0, right: 1, top: 0, bottom: 1 },
    }),
];

interact('#box').draggable({
    inertia: true,
    modifiers: dragModifiers,
    listeners: {
    move (event) {
        const target = event.target;
        let x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
        let y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

        target.style.transform = `translate(${x}px, ${y}px)`;
        target.setAttribute('data-x', x);
        target.setAttribute('data-y', y);
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
    const mods = [
    // 保证不出父容器（边缘受限）
    interact.modifiers.restrictEdges({ outer: 'parent' }),
    // 最小尺寸
    interact.modifiers.restrictSize({ min: { width: 80, height: 60 } }),
    ];
    if (snapOn) {
    // 尺寸对齐网格
    mods.push(interact.modifiers.snapSize({
        targets: [ interact.snappers.grid({ x: 8, y: 8 }) ]
    }));
    }
    return mods;
}

// 可缩放
function setupResizable(){
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

        let x = parseFloat(target.getAttribute('data-x')) || 0;
        let y = parseFloat(target.getAttribute('data-y')) || 0;

        // 更新宽高
        target.style.width  = event.rect.width + 'px';
        target.style.height = event.rect.height + 'px';
        updateChip(event.rect.width, event.rect.height);

        // 从上/左缩放时需要补偿位移
        x += event.deltaRect.left;
        y += event.deltaRect.top;

        target.style.transform = `translate(${x}px, ${y}px)`;
        target.setAttribute('data-x', x);
        target.setAttribute('data-y', y);
        }
    }
    });
}
setupResizable();

// —— 按钮事件 ——
resetBtn.addEventListener('click', () => {
    // 尺寸与位置复位
    box.style.width = '320px';
    box.style.height = '180px';
    updateChip(320, 180);

    const x = 40, y = 40;
    box.style.transform = `translate(${x}px, ${y}px)`;
    box.setAttribute('data-x', x);
    box.setAttribute('data-y', y);
});

setBtn.addEventListener('click', async () => {
    const width = box.clientWidth;
    const height = box.clientHeight;
    const offset_x = parseInt(box.getAttribute('data-x'))+1;
    const offset_y = parseInt(box.getAttribute('data-y'))+1;
    console.log(width, height,offset_x,offset_y);

    const max_height=480
    const max_width=800
    const config = {
        height: width,
        weight: height,
        offset_h: offset_x,
        offset_w: max_width-height-offset_y
    };

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