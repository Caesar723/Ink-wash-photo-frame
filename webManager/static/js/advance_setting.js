




async function initchatai(){
    const response=await fetch("/api/chatai_info",{
        method:"POST",
        
    })
    const data=await response.json()
    const chat_api_token=data.chat_api_token
    const chat_base_url=data.chat_base_url
    const chat_model=data.chat_model

    document.getElementById("chat_api_token").value=chat_api_token
    document.getElementById("chat_base_url").value=chat_base_url
    document.getElementById("chat_model").value=chat_model
}

initchatai()


async function setchataiinfo(){
    const response=await fetch("/api/set_chatai_info",{
        method:"POST",
        body:JSON.stringify({
            "chat_api_token":document.getElementById("chat_api_token").value,
            "chat_base_url":document.getElementById("chat_base_url").value,
            "chat_model":document.getElementById("chat_model").value
        })
    })
    const data=await response.json()
    if(data.status=="success"){
        alert("设置成功")
    }else{
        alert("设置失败")
    }
}
document.getElementById("submit-chatai-info").addEventListener("click",async (e)=>{
    e.preventDefault()
    await setchataiinfo()
})