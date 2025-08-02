const configs = [
    { id: 'days',    max: 30, label: '天' },
    { id: 'hours',   max: 23, label: '时' },
    { id: 'minutes', max: 59, label: '分' },
  ];
  const itemH = 40;

  configs.forEach(cfg => {
    const sp = document.getElementById(cfg.id);
    const mask = sp.querySelector('.spinner-mask');

    for (let i = 0; i < 2; i++) {
        const topPad = document.createElement('div');
        topPad.className = 'spinner-item';
        topPad.style.height = itemH + 'px';
        sp.appendChild(topPad);
    }

    // 生成选项
    for (let i = 0; i <= cfg.max; i++) {
      const item = document.createElement('div');
      item.className = 'spinner-item';
      item.textContent = i.toString().padStart(2, '0') + cfg.label;
      sp.appendChild(item);
    }
    for (let i = 0; i < 2; i++) {
        const bottomPad = document.createElement('div');
        bottomPad.className = 'spinner-item';
        bottomPad.style.height = itemH + 'px';
        sp.appendChild(bottomPad);
    }

    // 计算并设置 mask 的 top 和 height
    function alignMask(sp, idx) {
      const mask = sp.querySelector('.spinner-mask');
      const itemH = 40;  // 每个项的高度
      // 计算中间区域的偏移量
      const centerOffset = 40*idx
      
      // 1. 定位 mask 的 top 和 height
      mask.style.top    = `${centerOffset}px`;
      mask.style.height = `${itemH}px`;
      mask.dataset.selectedIndex=idx-2;
    }
    //alignMask();
    //window.addEventListener('resize', alignMask);

    // 首次对齐到 0，并高亮
    setTimeout(() => {
      sp.scrollTop = 0 * itemH - (sp.clientHeight - itemH) / 2;
      highlight(sp, 2);
      alignMask(sp,2);
    }, 0);

    // 停滚后自动对齐并高亮
    let debounce;
    sp.addEventListener('scroll', () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => {
        const centerOffset = (sp.clientHeight - itemH) / 2;
        const idx = Math.round((sp.scrollTop + centerOffset) / itemH);
        sp.scrollTo({ top: idx * itemH - centerOffset, behavior: 'smooth' });
        highlight(sp, idx);
        alignMask(sp,idx);
      }, 100);
    });
  });

  function highlight(spinner, idx) {
    spinner.querySelectorAll('.spinner-item').forEach((it, i) => {
      it.classList.toggle('selected', i === idx);
    });
  }

  // 方向切换

  async function get_place_mode(){
    const response=await requestSender.get_place_mode();
    
    if(response==="horizontal"){
      
      document.getElementById('hor').checked=true;
      document.getElementById('ver').checked=false;
    }else{
      document.getElementById('ver').checked=true;
      document.getElementById('hor').checked=false;
    }
  }
  get_place_mode();
  
  document.querySelectorAll('input[name="orientation"]').forEach(inp => {
    inp.addEventListener('change', async (e) => {
        const status=await requestSender.change_place_mode(e.target.value);
        if(status=="success"){
            console.log("切换模式成功");
        }else{
            console.log("切换模式失败");
        }
    });
  });

  document.getElementById('submit-time').addEventListener('click', async () => {
    const daysIdx    = parseInt(document.getElementById('days').querySelector('.spinner-mask').dataset.selectedIndex, 10);
    const hoursIdx   = parseInt(document.getElementById('hours').querySelector('.spinner-mask').dataset.selectedIndex, 10);
    const minutesIdx = parseInt(document.getElementById('minutes').querySelector('.spinner-mask').dataset.selectedIndex, 10);
    

    const payload = {  days: daysIdx, hours: hoursIdx, minutes: minutesIdx };
    console.log('准备发送 →', payload);

    try {
      const res = await fetch('/api/setTime', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      alert('提交成功！');
    } catch (err) {
      console.error(err);
      alert('提交失败：' + err.message);
    }
  });


  async function init_module_list(){
    const response=await requestSender.get_module_list();
    console.log(response);

    const unused_components=document.getElementById('unused-components');
    const used_components=document.getElementById('used-components');

    response.module_list.forEach(module=>{
      const item=document.createElement('div');
      item.className='component-item';
      item.textContent=module;
      used_components.appendChild(item);
    });

    const unused_module_list=response.total_module_list.filter(module=>!response.module_list.includes(module));

    unused_module_list.forEach(module=>{
      const item=document.createElement('div');
      item.className='component-item';
      item.textContent=module;
      unused_components.appendChild(item);
    });
  }
  init_module_list();


  Sortable.create(document.getElementById('unused-components'), {
    group: 'components',            // 分组名称相同才能互通
    animation: 150,                 // 拖拽动画时长
    ghostClass: 'sortable-ghost',   // 拖拽时的占位样式
    chosenClass: 'sortable-chosen'
  });


  async function set_module_list(){
    const used_components=document.getElementById('used-components');
    const items = Array.from(used_components.querySelectorAll('.component-item'));
    const order = items.map(el => el.textContent);
    const status=await requestSender.set_module_list(order);
    if(status=="success"){
        console.log("设置模块列表成功");
    }else{
        console.log("设置模块列表失败");
    }
  }

  Sortable.create(document.getElementById('used-components'), {
    group: 'components',
    animation: 150,
    ghostClass: 'sortable-ghost',
    chosenClass: 'sortable-chosen',
    onAdd(evt) {
        set_module_list();

    },
    onRemove(evt) {
        set_module_list();
        
    }
  });

  

  // 可选：监听激活事件
  document.getElementById('used-components').addEventListener('sortupdate', evt => {
    console.log('已使用组件列表更新：', Array.from(evt.to.children)
      .filter(el => el.classList.contains('component-item'))
      .map(el => el.textContent));
  });

  document.getElementById('change-image').addEventListener('click', async () => {
    const button = document.getElementById('change-image');
    const btnText = button.querySelector('.btn-text');
    const spinner = button.querySelector('.spinner_change_image');
    button.disabled = true;
    btnText.textContent = "加载中";
    spinner.style.display = "inline-block";
    const status=await requestSender.change_image();
    if(status=="success"){
        console.log("更换图片成功");
    }else{
        console.log("更换图片失败");
    }
    button.disabled = false;
    btnText.textContent = "换一张图片";
    spinner.style.display = "none";
  });