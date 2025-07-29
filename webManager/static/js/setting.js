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
    }
    //alignMask();
    window.addEventListener('resize', alignMask);

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
  document.querySelectorAll('input[name="orientation"]').forEach(inp => {
    inp.addEventListener('change', e => {
      console.log('orientation →', e.target.value);
    });
  });

  document.getElementById('submit-time').addEventListener('click', async () => {
    const daysIdx    = parseInt(document.getElementById('days').dataset.selectedIndex, 10);
    const hoursIdx   = parseInt(document.getElementById('hours').dataset.selectedIndex, 10);
    const minutesIdx = parseInt(document.getElementById('minutes').dataset.selectedIndex, 10);
    const orientation= document.querySelector('input[name="orientation"]:checked').value;

    const payload = { orientation, days: daysIdx, hours: hoursIdx, minutes: minutesIdx };
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


  Sortable.create(document.getElementById('unused-components'), {
    group: 'components',            // 分组名称相同才能互通
    animation: 150,                 // 拖拽动画时长
    ghostClass: 'sortable-ghost',   // 拖拽时的占位样式
    chosenClass: 'sortable-chosen'
  });

  Sortable.create(document.getElementById('used-components'), {
    group: 'components',
    animation: 150,
    ghostClass: 'sortable-ghost',
    chosenClass: 'sortable-chosen'
  });

  // 可选：监听激活事件
  document.getElementById('used-components').addEventListener('sortupdate', evt => {
    console.log('已使用组件列表更新：', Array.from(evt.to.children)
      .filter(el => el.classList.contains('component-item'))
      .map(el => el.textContent));
  });