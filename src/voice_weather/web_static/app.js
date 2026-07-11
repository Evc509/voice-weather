const $ = id => document.getElementById(id);
let state, currentCity, currentWeather;

const icons = {Clear:'☀', Sunny:'☀', 'Mainly clear':'🌤', 'Partly cloudy':'⛅', Overcast:'☁', Fog:'≋', 'Light rain':'🌦', 'Moderate rain':'🌧', 'Heavy rain':'🌧', 'Light snow':'🌨', 'Moderate snow':'❄', Thunderstorm:'⛈'};
const locales = {zh:'zh-CN', en:'en-CA', fr:'fr-FR', es:'es-ES', ja:'ja-JP'};
const ui = {
  en:{language:'Language',places:'PLACES',cities:'Your cities',feels:'Feels like',humidity:'Humidity',wind:'Wind',pressure:'Pressure',outlook:'OUTLOOK',forecast:'Seven-day forecast',play:'Play weather'},
  zh:{language:'语言',places:'城市',cities:'我的城市',feels:'体感温度',humidity:'湿度',wind:'风速',pressure:'气压',outlook:'未来天气',forecast:'七天天气预报',play:'播放天气'},
  fr:{language:'Langue',places:'LIEUX',cities:'Vos villes',feels:'Ressenti',humidity:'Humidité',wind:'Vent',pressure:'Pression',outlook:'PRÉVISIONS',forecast:'Prévisions sur sept jours',play:'Écouter la météo'},
  es:{language:'Idioma',places:'LUGARES',cities:'Tus ciudades',feels:'Sensación',humidity:'Humedad',wind:'Viento',pressure:'Presión',outlook:'PRONÓSTICO',forecast:'Pronóstico de siete días',play:'Escuchar el tiempo'},
  ja:{language:'言語',places:'場所',cities:'都市',feels:'体感温度',humidity:'湿度',wind:'風速',pressure:'気圧',outlook:'予報',forecast:'7日間予報',play:'天気を再生'}
};
const cityUi = {
  en:['Add a city','City, region or country','Search','Search first, then confirm one available location.','Add selected city','Delete this city?'],
  zh:['添加城市','城市、地区或国家','查找','请先查找，再确认一个可用地点。','添加所选城市','确定删除这个城市吗？'],
  fr:['Ajouter une ville','Ville, région ou pays','Rechercher','Recherchez puis confirmez un lieu disponible.','Ajouter la ville sélectionnée','Supprimer cette ville ?'],
  es:['Añadir ciudad','Ciudad, región o país','Buscar','Busque y confirme una ubicación disponible.','Añadir ciudad seleccionada','¿Eliminar esta ciudad?'],
  ja:['都市を追加','都市、地域、国','検索','検索して利用可能な場所を確認してください。','選択した都市を追加','この都市を削除しますか？']
};
const healthUi = {
  en:{aqi:'Air quality',uv:'UV index',good:'Air quality is good.',moderate:'Sensitive people should limit prolonged outdoor activity.',poor:'Consider reducing outdoor activity.',highUv:'UV is high; use sun protection.',rain:'Precipitation',wind:'Max wind',sunrise:'Sunrise',sunset:'Sunset'},
  zh:{aqi:'空气质量',uv:'紫外线指数',good:'空气质量良好。',moderate:'敏感人群应减少长时间户外活动。',poor:'建议减少户外活动。',highUv:'紫外线较强，请注意防晒。',rain:'降水量',wind:'最大风速',sunrise:'日出',sunset:'日落'},
  fr:{aqi:'Qualité de l’air',uv:'Indice UV',good:'La qualité de l’air est bonne.',moderate:'Les personnes sensibles devraient limiter les activités prolongées.',poor:'Réduisez les activités en plein air.',highUv:'UV élevé ; protégez-vous du soleil.',rain:'Précipitations',wind:'Vent maximal',sunrise:'Lever',sunset:'Coucher'},
  es:{aqi:'Calidad del aire',uv:'Índice UV',good:'La calidad del aire es buena.',moderate:'Las personas sensibles deben limitar la actividad prolongada.',poor:'Reduzca la actividad al aire libre.',highUv:'UV alto; use protección solar.',rain:'Precipitación',wind:'Viento máximo',sunrise:'Amanecer',sunset:'Atardecer'},
  ja:{aqi:'大気質',uv:'UV指数',good:'大気質は良好です。',moderate:'敏感な方は長時間の屋外活動を控えてください。',poor:'屋外活動を減らしてください。',highUv:'紫外線が強いため、日焼け対策をしてください。',rain:'降水量',wind:'最大風速',sunrise:'日の出',sunset:'日の入'}
};
const metaUi={en:{version:'local web app',privacy:'Location stays city-level. The local service only listens on this Mac.',source:'Weather data by Open-Meteo.com',voice:'Voice',text:'Text only',playing:'Playing weather',setLocation:'Set your location in voice-weather-cli settings'},zh:{version:'本地网页应用',privacy:'定位只保留城市级信息，本地服务仅在这台 Mac 上运行。',source:'天气数据由 Open-Meteo.com 提供',voice:'语音',text:'仅文字',playing:'正在播放天气',setLocation:'请先在 voice-weather-cli 设置当前位置'},fr:{version:'application web locale',privacy:'La localisation reste au niveau de la ville. Le service fonctionne uniquement sur ce Mac.',source:'Données météo par Open-Meteo.com',voice:'Voix',text:'Texte uniquement',playing:'Lecture de la météo',setLocation:'Définissez votre position dans voice-weather-cli'},es:{version:'aplicación web local',privacy:'La ubicación se mantiene a nivel de ciudad. El servicio solo funciona en este Mac.',source:'Datos meteorológicos de Open-Meteo.com',voice:'Voz',text:'Solo texto',playing:'Reproduciendo el tiempo',setLocation:'Configure su ubicación en voice-weather-cli'},ja:{version:'ローカルWebアプリ',privacy:'位置情報は都市レベルのみで、このMac上だけで動作します。',source:'気象データ: Open-Meteo.com',voice:'音声',text:'テキストのみ',playing:'天気を再生中',setLocation:'voice-weather-cliで現在地を設定してください'}};
const stopUi={en:['Stop','Playback stopped'],zh:['停止','播放已停止'],fr:['Arrêter','Lecture arrêtée'],es:['Detener','Reproducción detenida'],ja:['停止','再生を停止しました']};

const showToast = message => { const el=$('toast'); el.textContent=message; el.classList.add('show'); setTimeout(()=>el.classList.remove('show'),2600); };
const api = async (url, options) => { const response=await fetch(url,options); const data=await response.json(); if(!response.ok) throw new Error(data.error||'Request failed'); return data; };
const cityName = city => city.labels?.[state.language] || (state.language==='zh' && city.zh ? city.zh : city.city.split(',')[0]);
const weatherIcon = description => icons[description] || '◌';

function applyLanguage(){
  const text=ui[state.language]||ui.en, cityText=cityUi[state.language]||cityUi.en, health=healthUi[state.language]||healthUi.en, meta=metaUi[state.language]||metaUi.en;
  $('language-label').textContent=text.language; $('places-label').textContent=text.places; $('cities-heading').textContent=text.cities;
  $('feels-label').textContent=text.feels; $('humidity-label').textContent=text.humidity; $('wind-label').textContent=text.wind; $('pressure-label').textContent=text.pressure;
  $('outlook-label').textContent=text.outlook; $('forecast-heading').textContent=text.forecast; $('speak').textContent=`▶ ${text.play}`;
  $('dialog-title').textContent=cityText[0]; $('city-name-label').textContent=cityText[1]; $('search-city').textContent=cityText[2]; $('search-help').textContent=cityText[3]; $('save-city').textContent=cityText[4];
  $('aqi-label').textContent=health.aqi; $('uv-label').textContent=health.uv; document.documentElement.lang=state.language;
  $('version').textContent=`Version ${state.version} · ${meta.version}`; $('privacy-text').textContent=meta.privacy; $('source-text').textContent=meta.source; $('voice-status').textContent=state.voice?`${meta.voice}: ${state.voice}`:meta.text;
  $('stop-speak').textContent=`■ ${(stopUi[state.language]||stopUi.en)[0]}`;
}

function renderCities(){
  const root=$('cities'); root.innerHTML='';
  state.cities.forEach(city=>{
    const button=document.createElement('button'); button.className='city-button'+(currentCity===city.city?' active':'');
    button.innerHTML=`<span class="city-icon">${city.local?'⌖':'☆'}</span><span class="city-label"><strong>${cityName(city)}</strong></span>${city.local?'':'<span class="city-edit">×</span>'}`;
    button.onclick=()=>{ if(city.unset) return showToast((metaUi[state.language]||metaUi.en).setLocation); loadCity(city.city); };
    const edit=button.querySelector('.city-edit'); if(edit) edit.onclick=async event=>{ event.stopPropagation(); if(!confirm((cityUi[state.language]||cityUi.en)[5])) return; const index=state.favorites.findIndex(item=>item.city===city.city); try{await api('/api/cities',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'delete',index})});location.reload()}catch(error){showToast(error.message)} };
    root.appendChild(button);
  });
}

async function loadCity(city){
  currentCity=city; renderCities(); $('hero').classList.add('loading-card');
  try { const lang=state.language,selected=state.cities.find(item=>item.city===city),coordinates=selected?.latitude!==undefined?`&latitude=${selected.latitude}&longitude=${selected.longitude}`:''; const [now,outlook]=await Promise.all([api(`/api/weather?city=${encodeURIComponent(city)}&language=${lang}${coordinates}`),api(`/api/forecast?city=${encodeURIComponent(city)}&language=${lang}&days=7${coordinates}`)]); currentWeather=now.weather; renderWeather(now); renderForecast(outlook.forecast); }
  catch(error){ showToast(error.message); } finally { $('hero').classList.remove('loading-card'); }
}

function renderWeather(data){
  const weather=data.weather, health=healthUi[state.language]||healthUi.en;
  const selected=state.cities.find(city=>city.city===data.city); $('city-name').textContent=cityName(selected||{city:data.city}); $('condition').textContent=weather.description_localized; $('weather-icon').textContent=weatherIcon(weather.description); $('temperature').textContent=`${weather.temperature_c}°`;
  $('feels').textContent=`${weather.feels_like_c}°`; $('humidity').textContent=`${weather.humidity}%`; $('wind').textContent=`${weather.wind_kph} km/h`; $('pressure').textContent=`${weather.pressure_hpa} hPa`;
  $('aqi').textContent=weather.aqi; $('uv').textContent=weather.uv_index; $('pm25').textContent=`${weather.pm2_5} μg/m³`; $('pm10').textContent=`${weather.pm10} μg/m³`; $('local-time').textContent=weather.local_time.replace('T',' · ');
  const notes=[]; if(Number(weather.aqi)<=50) notes.push(health.good); else if(Number(weather.aqi)<=100) notes.push(health.moderate); else notes.push(health.poor); if(Number(weather.uv_index)>=6) notes.push(health.highUv); $('health-advice').textContent=notes.join(' ');
}

function renderForecast(days){
  const health=healthUi[state.language]||healthUi.en, locale=locales[state.language]||locales.en;
  $('forecast').innerHTML=days.map(day=>{ const date=new Date(`${day.date}T12:00:00`); return `<button class="forecast-day" type="button"><div class="day">${date.toLocaleDateString(locale,{weekday:'short'})} · ${date.toLocaleDateString(locale,{month:'short',day:'numeric'})}</div><div class="symbol">${weatherIcon(day.description)}</div><div class="range">${day.max_c}° <span style="color:var(--muted)">${day.min_c}°</span></div><div class="rain">♢ ${day.rain_chance}%</div><div class="forecast-detail"><div>${health.rain}: ${day.precipitation_mm} mm</div><div>${health.wind}: ${day.wind_max_kph} km/h</div><div>UV: ${day.uv_index}</div><div>${health.sunrise}: ${day.sunrise}</div><div>${health.sunset}: ${day.sunset}</div></div></button>`; }).join('');
  document.querySelectorAll('.forecast-day').forEach(card=>card.onclick=()=>card.classList.toggle('expanded'));
}

async function init(){
  try { state=await api('/api/state'); $('language').innerHTML=Object.entries(state.languages).map(([code,name])=>`<option value="${code}" ${code===state.language?'selected':''}>${name}</option>`).join(''); applyLanguage(); renderCities(); const first=state.cities.find(city=>!city.unset); if(first) loadCity(first.city); }
  catch(error){ showToast(error.message); }
}

let selectedCandidate=null;
function openCityDialog(){selectedCandidate=null;$('city-input').value='';$('city-results').innerHTML='';$('save-city').disabled=true;$('city-dialog').showModal()}

$('language').onchange=async event=>{ await api('/api/preferences',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({language:event.target.value})}); location.reload(); };
$('refresh').onclick=()=>currentCity&&loadCity(currentCity); $('add-city').onclick=()=>openCityDialog();
$('dialog-close').onclick=()=>$('city-dialog').close();
$('speak').onclick=async()=>{ if(!currentWeather)return; const selected=state.cities.find(city=>city.city===currentCity); try{ await api('/api/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({city:currentCity,label:selected?cityName(selected):currentCity,language:state.language})}); showToast((metaUi[state.language]||metaUi.en).playing); }catch(error){ showToast(error.message); } };
$('stop-speak').onclick=async()=>{try{await api('/api/speech/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});showToast((stopUi[state.language]||stopUi.en)[1])}catch(error){showToast(error.message)}};
$('search-city').onclick=async()=>{const query=$('city-input').value.trim();if(!query)return;try{const data=await api(`/api/cities/search?q=${encodeURIComponent(query)}&language=${state.language}`);selectedCandidate=null;$('save-city').disabled=true;$('city-results').innerHTML=data.results.map((item,index)=>`<button class="city-result" type="button" data-index="${index}"><strong>${item.name}</strong><small>${[item.region,item.country].filter(Boolean).join(', ')}</small></button>`).join('');document.querySelectorAll('.city-result').forEach(button=>button.onclick=()=>{document.querySelectorAll('.city-result').forEach(item=>item.classList.remove('selected'));button.classList.add('selected');selectedCandidate=data.results[Number(button.dataset.index)];$('save-city').disabled=false})}catch(error){showToast(error.message)}};
$('city-form').onsubmit=async event=>{event.preventDefault();if(!selectedCandidate)return;try{await api('/api/cities',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'add',city:selectedCandidate.canonical,name:selectedCandidate.name,latitude:selectedCandidate.latitude,longitude:selectedCandidate.longitude,language:state.language})});$('city-dialog').close();location.reload()}catch(error){showToast(error.message)}};
init();
