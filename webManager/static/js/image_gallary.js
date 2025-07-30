
  const overlay = document.getElementById('overlay');
  const overlayImg = document.getElementById('overlay-img');
  const closeBtn = document.querySelector('.overlay-close');
  const confirmBtn = document.querySelector('.overlay-confirm');
  const deleteBtn = document.querySelector('.overlay-delete');

  // 你现有的：点击缩略图打开预览


  // 关闭预览
  closeBtn.addEventListener('click', () => {
    overlay.style.display = 'none';
    resetDeleteState();
  });
  overlay.addEventListener('click', e => {
    if (e.target === overlay) {
      overlay.style.display = 'none';
      resetDeleteState();
    }
  });

  // 使用图片
  confirmBtn.addEventListener('click', async () => {
    console.log('发送图片:', overlayImg.src,overlayImg.title);
    
    overlay.style.display = 'none';
    resetDeleteState();
    const status=await requestSender.use_image(overlayImg.title);
    console.log(status);
    
  });

  // —— 删除相关 —— //
  let deleteArmed = false;     // 是否处于“待删除”状态（已点第一次）
  let deleteTimer = null;      // 超时计时器
  const ARMED_TIMEOUT = 3000;  // 第二次点击的限定时间（毫秒），可按需调整

  // 第一次点击：进入 armed 状态并变红；第二次点击：真正删除
  deleteBtn.addEventListener('click', () => {
    if (!deleteArmed) {
      armDelete();
    } else {
      performDelete(overlayImg.src,overlayImg.title);
    }
  });

  // 也可支持双击（可选）：如果用户直接 dblclick 也触发删除
  deleteBtn.addEventListener('dblclick', (e) => {
    e.preventDefault();
    performDelete(overlayImg.src,overlayImg.title);
  });

  function armDelete() {
    deleteArmed = true;
    deleteBtn.classList.add('armed');

    // 创建/重置倒计时：超时后自动恢复
    clearTimeout(deleteTimer);
    deleteTimer = setTimeout(() => {
      resetDeleteState();
    }, ARMED_TIMEOUT);
  }

  function resetDeleteState() {
    deleteArmed = false;
    deleteBtn.classList.remove('armed');
    clearTimeout(deleteTimer);
    deleteTimer = null;
  }

  async function performDelete(imgSrc,index) {
    // 真正发送删除请求前先复位 UI 状态
    resetDeleteState();
    const status=await requestSender.delete_image(index);
    if(status=="success"){
      const container=document.getElementById(index+"_container");
      container.remove();
    }

    console.log('发送删除请求:', imgSrc);
    

    // 删除成功后的 UI 行为（可按需要调整）
    overlay.style.display = 'none';
  }

  async function initinal_img(){
    const index_list = await requestSender.get_img_index();
    console.log(index_list);
    const gallery_container = document.getElementById('gallery-container');
    for(let i=0;i<index_list.length;i++){
        const container=document.createElement('div');
        container.classList.add('col');
        container.id=index_list[i]+"_container";
        container.innerHTML = `
        <img
            src="/static/images/shored_img/${index_list[i]}"
            class="img-fluid rounded shadow-sm gallery-img"
            loading="lazy"
            title="${index_list[i]}"
        />
        `;
        gallery_container.appendChild(container);
    }



    document.querySelectorAll('.gallery-img').forEach(img => {
        img.addEventListener('click', () => {
          overlayImg.src = img.src;
          overlayImg.title = img.title;
          overlay.style.display = 'flex';
          resetDeleteState();
        });
    });
  }


  initinal_img();

