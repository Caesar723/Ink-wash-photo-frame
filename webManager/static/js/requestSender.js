


class RequestSender{
   

    async send_request(url,data={}){
        const base_url="/api/"
        const response = await fetch(base_url+url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        return response.json();
    }


    async get_img_index(){
        const response = await this.send_request("get_img_index");
        
    }


    async use_image(index){
        data={
            "index":index
        }
        const response = await this.send_request("use_image",data=data);
        
    }

    async change_place_mode(mode){
        data={
            "mode":mode
        }
        const response = await this.send_request("change_place_mode",data=data);
        
    }

    async set_time_gap(time_gap){
        data={
            "time_gap":time_gap
        }
        const response = await this.send_request("set_time_gap",data=data);
        
    }

    async set_module_list(module_list){
        data={
            "module_list":module_list
        }
        const response = await this.send_request("set_module_list",data=data);
        
    }
}

const requestSender = new RequestSender();