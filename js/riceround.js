import{api}from"../../../scripts/api.js";import{ComfyApp,app}from"../../../scripts/app.js";const GetHost=()=>{const{protocol:e,hostname:t,port:o}=window.location,n=parseInt(o,10);let i=t;return 80===n&&"http:"===e||443===n&&"https:"===e?i=t:isNaN(n)||0===n||(i=`${t}:${o}`),i};function loadToastScript(){return new Promise(((e,t)=>{const o=document.createElement("script");o.src="https://cdn.jsdelivr.net/npm/toastify-js",o.onload=e,o.onerror=t,document.head.appendChild(o);const n=document.createElement("link");n.href="https://cdn.jsdelivr.net/npm/toastify-js/src/toastify.min.css",n.type="text/css",n.rel="stylesheet",document.head.appendChild(n)}))}let toastHasLoaded=!1;async function loadToast(){toastHasLoaded||(await loadToastScript(),toastHasLoaded=!0)}export async function showToast(e,t="info",o=3e3){await loadToast(),"info"==t?Toastify({text:e,duration:o,close:!1,gravity:"top",position:"center",stopOnFocus:!1}).showToast():"error"==t?Toastify({text:e,duration:o,close:!0,gravity:"top",position:"center",backgroundColor:"#FF4444",stopOnFocus:!0}).showToast():"warning"==t&&Toastify({text:e,duration:o,close:!0,gravity:"top",position:"center",backgroundColor:"#FFA500",stopOnFocus:!0}).showToast()}function loadMessageBoxScript(){return new Promise(((e,t)=>{const o=document.createElement("script");o.src="https://cdn.jsdelivr.net/npm/sweetalert2@11",o.onload=e,o.onerror=t,document.head.appendChild(o)}))}let messageBoxHasLoaded=!1;async function loadMssageBox(){messageBoxHasLoaded||(await loadMessageBoxScript(),messageBoxHasLoaded=!0)}export async function showHtmlMessageBox(e,t,o,n,i){await loadMssageBox(),Swal.fire({title:e,html:t,icon:o,confirmButtonText:n,preConfirm:()=>{i&&(window.location.href=i)}})}async function setNodeAdditionalInfo(e){try{const t={method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(e)},o=await api.fetchApi("/riceround/set_node_additional_info",t);await o.json()}catch(e){console.error("riceround set_node_additional_info error",e)}}function changeWidget(e,t,o,n){e.type=t,e.value=o,e.options=n}function changeWidgets(e,t,o,n){"customtext"===t&&(t="text"),console.log("changeWidgets",e,t,o,n);const i=n.options;var a=e.widgets[1].value;i?.values?.includes(a)||(a=n.value),"RiceRoundAdvancedChoiceNode"==e.comfyClass||"RiceRoundSimpleChoiceNode"==e.comfyClass?changeWidget(e.widgets[1],t,a,i):"RiceRoundIntNode"!=e.comfyClass&&"RiceRoundFloatNode"!=e.comfyClass||4==e.widgets.length&&(changeWidget(e.widgets[1],"number",a,i),changeWidget(e.widgets[2],"number",i?.min??0,i),changeWidget(e.widgets[3],"number",i?.max??100,i))}function adaptWidgetsBasedOnConnection(e,t,o,n){if(e.outputs[0].type=o.type,"name"===e.widgets[0].label){(["数值","文本","列表","参数","Parameter"].includes(e.widgets[0].value)||""==e.widgets[0].value)&&(e.widgets[0].value=o.label?o.label:o.name)}const i=o.widget?.name?o.widget?.name:o.name,a=t.widgets.find((e=>e.name===i));if(!a)return;changeWidgets(e,a.origType??a.type,t,a)}api.addEventListener("rice_round_toast",(e=>{showToast(e.detail.content,e.detail.type,e.detail.duration)})),api.addEventListener("rice_round_login",(e=>{const t=e.detail.machine_id,o=e.detail.url_prefix,n=GetHost(),i=`${window.location.protocol}//${n}`,a=`${o}/auth/login?machine_id=${t}&callback_url=${btoa(`${i}/riceround/auth_callback`)}`;showHtmlMessageBox("登录",`RiceRound登录失效，请<a href="${a}" target="_blank">点击链接</a>重新登录`,"info","确定",a)})),api.addEventListener("execution_start",(async({detail:e})=>{let t="";const o={};for(const e of app.graph.nodes){if("RiceRoundDecryptNode"===e.type)return;if("RiceRoundEncryptNode"===e.type){const o=e.widgets?.find((e=>"template_id"===e.name&&e.value));if(o){if(t)return;t=o.value}}else if("RiceRoundAdvancedChoiceNode"===e.type||"RiceRoundSimpleChoiceNode"===e.type){if(1===!e.outputs?.[0]?.links?.length)continue;const t=e.widgets[1].options?.values??[];if(!t.length)continue;const n=e.graph.links[e.outputs[0].links[0]];if(!n)continue;const i=e.graph.getNodeById(n.target_id);if(!i?.inputs||"RiceRoundDecryptNode"===i.comfyClass||"RiceRoundEncryptNode"===i.comfyClass)continue;const a=i.inputs[n.target_slot];if(!a||!i.widgets)continue;const s=a.widget?.name||a.name;if(!s)continue;const d=`${i.comfyClass}.${s}`;o[e.id]={class_name:d,options_value:t,node_type:e.type}}}t&&Object.keys(o).length>0&&await setNodeAdditionalInfo({choice_node_map:o,template_id:t})}));let applySimpleChoiceNodeExtraLogicTimer=null;function applySimpleChoiceNodeExtraLogic(e,t){applySimpleChoiceNodeExtraLogicTimer&&clearTimeout(applySimpleChoiceNodeExtraLogicTimer),applySimpleChoiceNodeExtraLogicTimer=setTimeout((()=>{applySimpleChoiceNodeExtraLogicTimer=null;const o=t.graph.extra?.choice_node_map;if(e&&e.widgets&&2===e.widgets.length&&o&&o[e.id]){const t={values:o[e.id]};changeWidget(e.widgets[1],"combo",e.widgets[1].value,t)}}),200)}function adaptWidgetsToConnection(e){if(!e.outputs||0===e.outputs.length)return;const t=e.outputs[0].links;if(t&&1===t.length){const o=e.graph.links[t[0]];if(!o)return;const n=e.graph.getNodeById(o.target_id);if(!n||!n.inputs)return;if("RiceRoundDecryptNode"==n.comfyClass&&"RiceRoundSimpleChoiceNode"==e.comfyClass)return console.log("applySimpleChoiceNodeExtraLogic",e),void applySimpleChoiceNodeExtraLogic(e,app);if("RiceRoundEncryptNode"==n.comfyClass||"RiceRoundDecryptNode"==n.comfyClass)return;const i=n.inputs[o.target_slot];if(!i||void 0===n.widgets)return;adaptWidgetsBasedOnConnection(e,n,i,app)}else t&&0!==t.length||("RiceRoundAdvancedChoiceNode"==e.comfyClass||"RiceRoundSimpleChoiceNode"==e.comfyClass?(e.widgets[0].value="Parameter",e.outputs[0].type="*"):"RiceRoundIntNode"==e.comfyClass?4==e.widgets.length&&(e.widgets[0].value="数值",e.widgets[1].value=0,e.widgets[2].value=0,e.widgets[3].value=100):"RiceRoundFloatNode"==e.comfyClass&&4==e.widgets.length&&(e.widgets[0].value="数值",e.widgets[1].value=0,e.widgets[2].value=0,e.widgets[3].value=100))}function setupParameterNode(e){const t=e.prototype.onAdded;e.prototype.onAdded=function(){t?.apply(this,arguments),adaptWidgetsToConnection(this)};const o=e.prototype.onAfterGraphConfigured;e.prototype.onAfterGraphConfigured=function(){o?.apply(this,arguments),adaptWidgetsToConnection(this)};const n=e.prototype.onConnectOutput;e.prototype.onConnectOutput=function(e,t,o,i,a){return!(!o.widget&&!(o.type in["STRING","COMBO","combo"]))&&(!n||(result=n.apply(this,arguments),result))};const i=e.prototype.onConnectionsChange;e.prototype.onConnectionsChange=function(e,t,o,n,a){return 2!=e||o||!this?.type||"RiceRoundAdvancedChoiceNode"!=this.type&&"RiceRoundSimpleChoiceNode"!=this.type||(this.widgets[0].value="Parameter"),app.configuringGraph||adaptWidgetsToConnection(this),i?.apply(this,arguments)}}function generateUUID(){let e="";for(let t=0;t<32;t++){e+=Math.floor(16*Math.random()).toString(16)}return e}app.registerExtension({name:"riceround.custom",async beforeRegisterNodeDef(e,t,o){["RiceRoundAdvancedChoiceNode","RiceRoundSimpleChoiceNode","RiceRoundIntNode","RiceRoundFloatNode"].includes(t.name)&&setupParameterNode(e)},nodeCreated(e,t){if("RiceRoundEncryptNode"==e.comfyClass&&e.widgets&&e.widgets.length>0){const t=window.document.title;if(t){let o=t.replace(/\s*-\s*ComfyUI$/,"").replace(/[<>:"/\\|?*]/g,"_").replace(/^[^a-zA-Z]+|[^a-zA-Z]+$/g,"");for(let t=0;t<e.widgets.length;t++){let n=e.widgets[t];if("project_name"==n.name&&(""==n.value||null==n.value||"my_project"==n.value)){n.value=o;break}}}e.widgets.push({name:"generate_uuid",type:"button",label:"Generate UUID",callback:()=>{const t=generateUUID();for(let o=0;o<e.widgets.length;o++){let n=e.widgets[o];if("template_id"==n.name){n.value=t;break}}}});const o=document.getElementById(e.id);o&&o.appendChild(button)}},async setup(){const e=`${window.location.protocol}//${api_host}`;try{const t={method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({local_base_url:e,host:window.location.hostname,port:window.location.port,protocol:window.location.protocol})},o=await api.fetchApi("/riceround/set_comfyui_web_server_info",t),n=await o.json();if(!o.ok)return void console.error("Error:",n.error)}catch(e){console.error("Request failed:",e)}}});