


class RequestSender{
   

    async send_request(url,data={}){
        const base_url="/api/"
        const response = await fetch(base_url+url, {
            method: 'POST',
            body: JSON.stringify(data)
        });

        const result=await response.json();
        console.log(result);
        return result;
    }


    async get_img_index(){
        const response = await this.send_request("get_img_index");
        return response.index_list;
    }


    async use_image(index){
        const send_data={
            "index":index
        }
        const response = await this.send_request("use_image",send_data);
        return response.status;
    }

    async delete_image(index){
        const send_data={
            "index":index
        }
        const response = await this.send_request("delete_image",send_data);
        return response.status;
    }

    async change_place_mode(mode){
        const send_data={
            "mode":mode
        }
        const response = await this.send_request("change_place_mode",send_data);
        return response.status;
    }

    async set_time_gap(time_gap){
        const send_data={
            "time_gap":time_gap
        }
        const response = await this.send_request("set_time_gap",send_data);
        
    }

    async get_module_list(){
        
        const response = await this.send_request("get_module_list");
        return response;
    }

    async set_module_list(module_list){
        const send_data={
            "module_list":module_list
        }
        const response = await this.send_request("set_module_list",send_data);
        return response.status;
    }

    async set_city(city){
        const send_data={
            "city":city
        }
        const response = await this.send_request("set_city",send_data);
        return response.status;
    }
}

const requestSender = new RequestSender();