import { Country, State, City } from '/static/js/country_list.js';
// DOM
const $country = document.getElementById('country');
const $state   = document.getElementById('state');
const $city    = document.getElementById('city');


const $hintCountry = document.getElementById('country-hint');
const $hintState   = document.getElementById('state-hint');
const $hintCity    = document.getElementById('city-hint');


const $result  = document.getElementById('result');
const $select_city=document.getElementById('select-city');
const $rQ      = document.getElementById('r-q');

const $picker = document.getElementById('picker');
$picker.style.gridTemplateColumns = '1fr'

// 工具：填充 select
function fillSelect(sel, items, getValue, getText, placeholder, disableIfEmpty = true) {
    sel.innerHTML = '';
    const ph = document.createElement('option');
    ph.value = '';
    ph.textContent = placeholder;
    sel.appendChild(ph);

    items.forEach(it => {
    const opt = document.createElement('option');
    opt.value = getValue(it);
    opt.textContent = getText(it);
    sel.appendChild(opt);
    });

    sel.disabled = disableIfEmpty && items.length === 0;
    sel.value = '';
}

// 1) 国家
const countries = Country.getAllCountries(); // [{name, isoCode, ...}]
fillSelect($country, countries, c => c.isoCode, c => `${c.name}（${c.isoCode}）`, '请选择国家', false);
$hintCountry.textContent = `共 ${countries.length} 个国家/地区`;

// 2) 国家 → 省/州
$country.addEventListener('change', () => {
    $result.hidden = true;
    
    const c = $country.value;

    // 重置
    fillSelect($state, [], s=>s, s=>s, '请选择省/州');
    fillSelect($city,  [], s=>s, s=>s, '请选择城市');
    
    

    if (!c) { $hintState.textContent='选择国家后加载'; $hintCity.textContent='选择省/州后加载'; return; }

    const states = State.getStatesOfCountry(c); // [{name, isoCode, ...}]
    fillSelect($state, states, s => s.isoCode, s => s.name, states.length ? '请选择省/州' : '（该国无省/州数据）');
    $hintState.textContent = states.length ? `共 ${states.length} 个省/州` : '该国没有省/州数据';

    // 若无省/州，直接按国家加载城市
    if (states.length === 0) {
    const cities = City.getCitiesOfCountry(c);
    fillSelect($city, cities, x => x.name, x => x.name, cities.length ? '请选择城市' : '（无城市数据）');
    $hintCity.textContent = cities.length ? `该国共 ${cities.length} 个城市` : '未提供城市数据';
    
    } else {
    $hintCity.textContent = '选择省/州后加载';
    }
});

// 3) 省/州 → 城市（含搜索过滤）
let currentCities = [];

$select_city.addEventListener('click',async ()=>{
    const c = $country.value, s = $state.value, cityName = $city.value;
    if (!c || !cityName) { $result.hidden = true ; return; }
    // 在两种来源里找城市（按省或按国）
    let city = null;
    if (s) city = City.getCitiesOfState(c, s).find(x => x.name === cityName);
    if (!city) city = City.getCitiesOfCountry(c).find(x => x.name === cityName);
    const q = `${cityName},${c.toLowerCase()}`;
    
    $rQ.textContent       = q;
    const status=await requestSender.set_city(q);
    if(status=="success"){
        alert("选择城市成功");
    }else{
        alert("选择城市失败");
    }
});

$state.addEventListener('change', () => {
    $result.hidden = true;
    
    const c = $country.value, s = $state.value;

    if (!c) return;

    if (!s) {
    currentCities = City.getCitiesOfCountry(c);
    } else {
    currentCities = City.getCitiesOfState(c, s);
    }
    fillSelect($city, currentCities, x => x.name, x => x.name, currentCities.length ? '请选择城市' : '（无城市数据）');
    $hintCity.textContent = currentCities.length ? `共 ${currentCities.length} 个城市` : '未提供城市数据';

});



// // 4) 城市 → 结果
// $city.addEventListener('change', () => {
//     const c = $country.value, s = $state.value, cityName = $city.value;
//     if (!c || !cityName) { $result.hidden = true ; return; }
//     // 在两种来源里找城市（按省或按国）
//     let city = null;
//     if (s) city = City.getCitiesOfState(c, s).find(x => x.name === cityName);
//     if (!city) city = City.getCitiesOfCountry(c).find(x => x.name === cityName);
//     const q = `${cityName},${c.toLowerCase()}`;
    
//     $rQ.textContent       = q;

    
//     $result.hidden = false;
    
// });
