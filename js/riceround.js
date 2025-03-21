import { api } from "../../../scripts/api.js";

import { ComfyApp, app } from "../../../scripts/app.js";

const style = document.createElement("style");

style.textContent = "\n    .riceround-swal-top-container {\n        z-index: 99999 !important;\n    }\n", 
document.head.appendChild(style);

export async function loadResource(e, t = "") {
    if (!document.querySelector(`script[src="${e}"]`)) {
        const t = document.createElement("script");
        t.src = e, document.head.appendChild(t);
        try {
            await new Promise(((o, n) => {
                t.onload = o, t.onerror = () => n(new Error(`Failed to load script: ${e}`));
            }));
        } catch (e) {}
    }
    if (t) {
        if (!document.querySelector(`link[href="${t}"]`)) {
            const e = document.createElement("link");
            e.rel = "stylesheet", e.href = t, document.head.appendChild(e);
            try {
                await new Promise(((o, n) => {
                    e.onload = o, e.onerror = () => n(new Error(`Failed to load stylesheet: ${t}`));
                }));
            } catch (e) {}
        }
    }
}

let toastHasLoaded = !1;

async function loadToast() {
    if (!toastHasLoaded) {
        const e = "https://cdn.jsdelivr.net/npm/toastify-js", t = "https://cdn.jsdelivr.net/npm/toastify-js/src/toastify.min.css";
        await loadResource(e, t), toastHasLoaded = !0;
    }
}

export async function showToast(e, t = "info", o = 3e3) {
    await loadToast(), "info" == t ? Toastify({
        text: e,
        duration: o,
        close: !1,
        gravity: "top",
        position: "center",
        backgroundColor: "#3498db",
        stopOnFocus: !1
    }).showToast() : "error" == t ? Toastify({
        text: e,
        duration: o,
        close: !0,
        gravity: "top",
        position: "center",
        backgroundColor: "#FF4444",
        stopOnFocus: !0
    }).showToast() : "warning" == t && Toastify({
        text: e,
        duration: o,
        close: !0,
        gravity: "top",
        position: "center",
        backgroundColor: "#FFA500",
        stopOnFocus: !0
    }).showToast();
}

let messageBoxHasLoaded = !1;

export async function loadMessageBox() {
    messageBoxHasLoaded || (await loadResource("https://cdn.jsdelivr.net/npm/sweetalert2@11", "https://cdn.jsdelivr.net/npm/@sweetalert2/theme-bootstrap-4/bootstrap-4.css"), 
    messageBoxHasLoaded = !0);
}

async function showClientInstallMessageBox(e, t) {
    const o = localStorage.getItem("riceround_client_dontshow");
    if (!(o && Number(o) > Date.now())) if (await loadMessageBox(), e) {
        if (!t) {
            const e = await Swal.fire({
                title: "Client未启动",
                html: '本机Client似乎没有启动，这不影响发布，但发布后可能没有算力可用，可以点击<a href="https://help.riceround.online/#/install?id=client-node-deployment" target="_blank">这里</a>寻求帮助，也可以尝试修复本机配置或打开Client文件夹查看详情。',
                icon: "warning",
                showCancelButton: !0,
                showDenyButton: !0,
                confirmButtonText: "修复配置",
                denyButtonText: "打开文件夹",
                cancelButtonText: "不再提示",
                heightAuto: !1,
                customClass: {
                    container: "riceround-swal-top-container"
                }
            });
            if (e.isConfirmed) await api.fetchApi("/riceround/fix_toml", {
                method: "Get"
            }); else if (e.isDenied) await api.fetchApi("/riceround/open_folder?id=1", {
                method: "GET"
            }); else if (e.dismiss === Swal.DismissReason.cancel) {
                const e = Date.now() + 2592e5;
                localStorage.setItem("riceround_client_dontshow", e.toString());
            }
        }
    } else {
        const e = await Swal.fire({
            title: "未安装Client",
            html: "您似乎没有安装Client，这样即使完成发布后，仍然可能没有算力支撑导致无法使用，详情请点击下方按钮查看并安装",
            icon: "warning",
            confirmButtonText: "查看安装说明",
            showCancelButton: !0,
            cancelButtonText: "不再提示",
            heightAuto: !1,
            customClass: {
                container: "riceround-swal-top-container"
            }
        });
        if (e.isConfirmed) window.open("https://help.riceround.online", "_blank"); else if (e.dismiss === Swal.DismissReason.cancel) {
            const e = Date.now() + 2592e5;
            localStorage.setItem("riceround_client_dontshow", e.toString());
        }
    }
}

function send_message(e, t) {
    api.fetchApi("/riceround/message", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            id: e,
            message: t
        })
    });
}

var skip_next = 0;

function send_onstart() {
    return skip_next > 0 ? (skip_next -= 1, !1) : (send_message(-1, "__start__"), !0);
}

async function serverShowMessageBox(e, t) {
    await loadMessageBox();
    const o = {
        ...e,
        heightAuto: !1
    };
    try {
        const e = await Swal.fire(o), n = {
            confirmed: e.isConfirmed ? 1 : 0,
            value: e.value,
            dismiss: e.dismiss
        };
        api.fetchApi("/riceround/message", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                id: t,
                message: n
            })
        });
    } catch (e) {
        api.fetchApi("/riceround/message", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                id: t,
                message: {
                    confirmed: 0,
                    error: e.message
                }
            })
        });
    }
    window.addEventListener("beforeunload", (function() {
        fetch("/riceround/message", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                id: t,
                message: "__cancel__"
            }),
            keepalive: !0
        });
    }), {
        once: !0
    });
}

api.addEventListener("riceround_toast", (e => {
    showToast(e.detail.content, e.detail.type, e.detail.duration);
})), api.addEventListener("riceround_server_dialog", (e => {
    serverShowMessageBox(JSON.parse(e.detail.json_content), e.detail.id);
})), api.addEventListener("riceround_client_install_dialog", (e => {
    showClientInstallMessageBox(e.detail.is_installed, e.detail.is_running);
}));

let dialogLibHasLoaded = !1;

async function waitForObject(e, t, o = 5e3) {
    return new Promise(((n, i) => {
        const a = Date.now(), s = () => {
            Date.now() - a > o ? i(new Error(`Timeout waiting for ${t} to load`)) : e() ? n() : setTimeout(s, 50);
        };
        s();
    }));
}

export async function initDialogLib(e = !1) {
    if (!dialogLibHasLoaded) try {
        const e = "https://cdn.bootcdn.net/ajax/libs/vue/3.3.4/vue.global.js";
        await loadResource(e, ""), await waitForObject((() => window.Vue), "vue");
        const t = "https://cdn.jsdelivr.net/npm/element-plus", o = "https://cdn.jsdelivr.net/npm/element-plus/dist/index.css";
        if (await loadResource(t, o), await waitForObject((() => window.ElementPlus), "element-plus"), 
        null == window.DialogLib) {
            const e = "riceround/static/dialog-lib.umd.cjs";
            await loadResource(e, ""), await waitForObject((() => window.DialogLib), "showLoginDialog");
        }
        dialogLibHasLoaded = !0;
    } catch (e) {
        throw e;
    }
}

async function setNodeAdditionalInfo(e) {
    try {
        const t = {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(e)
        }, o = await api.fetchApi("/riceround/set_node_additional_info", t);
        await o.json();
    } catch (e) {}
}

function changeWidget(e, t, o, n) {
    e.type = t, e.value = o, e.options = n;
}

function changeWidgets(e, t, o, n) {
    "customtext" === t && (t = "text");
    const i = n.options;
    var a = e.widgets[1].value;
    i?.values?.includes(a) || (a = n.value), "RiceRoundAdvancedChoiceNode" == e.comfyClass || "RiceRoundSimpleChoiceNode" == e.comfyClass ? "combo" === t ? setupComboWidget(e.widgets[1], e, 1, i.values) : changeWidget(e.widgets[1], t, a, i) : "RiceRoundIntNode" != e.comfyClass && "RiceRoundFloatNode" != e.comfyClass || 4 == e.widgets.length && (changeWidget(e.widgets[1], "number", a, i), 
    changeWidget(e.widgets[2], "number", i?.min ?? 0, i), changeWidget(e.widgets[3], "number", i?.max ?? 100, i));
}

function adaptWidgetsBasedOnConnection(e, t, o, n) {
    if (e.outputs[0].type = o.type, "name" === e.widgets[0].label) {
        ([ "数值", "文本", "列表", "参数", "Parameter" ].includes(e.widgets[0].value) || "" == e.widgets[0].value) && (e.widgets[0].value = o.label ? o.label : o.name);
    }
    const i = o.widget?.name ? o.widget?.name : o.name, a = t.widgets.find((e => e.name === i));
    if (!a) return;
    changeWidgets(e, a.origType ?? a.type, t, a);
}

api.addEventListener("riceround_login_dialog", (e => {
    const t = e.detail.client_key, o = e.detail.title;
    window.DialogLib.showLoginDialog({
        title: o,
        spyNetworkError: !0,
        mainKey: "riceround"
    }).then((e => {
        api.fetchApi("/riceround/auth_callback", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                token: e,
                client_key: t
            })
        }), showToast("登录成功");
    })).catch((e => {
        showToast("登录失败", "error");
    }));
})), api.addEventListener("riceround_show_workflow_payment_dialog", (e => {
    const t = e.detail.title ?? "支付", o = e.detail.template_id;
    o ? window.DialogLib.showWorkflowQRPaymentDialog({
        title: t,
        template_id: o
    }).then((({success: e, msg: t}) => {
        showToast(t, e ? "info" : "error");
    })).catch((e => {
        showToast("取消支付", "error");
    })) : showToast("模板ID不能为空", "error");
})), api.addEventListener("riceround_clear_user_info", (async e => {
    const t = e.detail.clear_key;
    "all" == t ? (localStorage.removeItem("Comfy.Settings.RiceRound.User.long_token"), 
    localStorage.removeItem("riceround_user_token"), app.ui.settings.setSettingValue("RiceRound.User.long_token", "")) : "long_token" == t ? (localStorage.removeItem("Comfy.Settings.RiceRound.User.long_token"), 
    app.ui.settings.setSettingValue("RiceRound.User.long_token", "")) : "user_token" == t && localStorage.removeItem("riceround_user_token");
})), api.addEventListener("execution_start", (async ({detail: e}) => {
    let t = "";
    const o = {};
    for (const e of app.graph.nodes) {
        if ("RiceRoundDecryptNode" === e.type) return;
        if ("RiceRoundEncryptNode" === e.type) {
            const o = e.widgets?.find((e => "template_id" === e.name && e.value));
            if (o) {
                if (t) return;
                t = o.value;
            }
        } else if ("RiceRoundAdvancedChoiceNode" === e.type || "RiceRoundSimpleChoiceNode" === e.type) {
            if (1 === !e.outputs?.[0]?.links?.length) continue;
            const t = e.widgets[1].options?.values ?? [];
            if (!t.length) continue;
            const n = e.graph.links[e.outputs[0].links[0]];
            if (!n) continue;
            const i = e.graph.getNodeById(n.target_id);
            if (!i?.inputs || "RiceRoundDecryptNode" === i.comfyClass || "RiceRoundEncryptNode" === i.comfyClass) continue;
            const a = i.inputs[n.target_slot];
            if (!a || !i.widgets) continue;
            const s = a.widget?.name || a.name;
            if (!s) continue;
            const d = `${i.comfyClass}.${s}`;
            o[e.id] = {
                class_name: d,
                options_value: t,
                node_type: e.type
            };
        }
    }
    t && Object.keys(o).length > 0 && await setNodeAdditionalInfo({
        choice_node_map: o,
        template_id: t
    }), send_onstart();
}));

const nodeTimersMap = new Map;

function setupComboWidget(e, t, o, n) {
    e.type = "combo", e.options = {
        values: n
    }, n.includes(e.value) || (e.value = n[0]);
    const i = t.id;
    e.callback = function(e) {
        const t = app.graph._nodes_by_id[i];
        t?.widgets?.[o] && (t.widgets[o].value = e, t.setDirtyCanvas(!0));
    };
}

function applySimpleChoiceNodeExtraLogic(e, t) {
    if (!e?.id) return;
    nodeTimersMap.has(e.id) && (clearTimeout(nodeTimersMap.get(e.id)), nodeTimersMap.delete(e.id));
    const o = setTimeout((() => {
        nodeTimersMap.delete(e.id);
        const o = t.graph.extra?.choice_node_map;
        2 === e?.widgets?.length && o?.[e.id] && (setupComboWidget(e.widgets[1], e, 1, o[e.id]), 
        e.setDirtyCanvas(!0));
    }), 200);
    nodeTimersMap.set(e.id, o);
}

function adaptWidgetsToConnection(e) {
    if (!e.outputs || 0 === e.outputs.length) return;
    const t = e.outputs[0].links;
    if (t && 1 === t.length) {
        const o = e.graph.links[t[0]];
        if (!o) return;
        const n = e.graph.getNodeById(o.target_id);
        if (!n || !n.inputs) return;
        if ("RiceRoundDecryptNode" == n.comfyClass && "RiceRoundSimpleChoiceNode" == e.comfyClass) return void applySimpleChoiceNodeExtraLogic(e, app);
        if ("RiceRoundEncryptNode" == n.comfyClass || "RiceRoundDecryptNode" == n.comfyClass) return;
        const i = n.inputs[o.target_slot];
        if (!i || void 0 === n.widgets) return;
        adaptWidgetsBasedOnConnection(e, n, i, app);
    } else t && 0 !== t.length || ("RiceRoundAdvancedChoiceNode" == e.comfyClass || "RiceRoundSimpleChoiceNode" == e.comfyClass ? (e.widgets[0].value = "Parameter", 
    e.outputs[0].type = "*") : "RiceRoundIntNode" == e.comfyClass ? 4 == e.widgets.length && (e.widgets[0].value = "数值", 
    e.widgets[1].value = 0, e.widgets[2].value = 0, e.widgets[3].value = 100) : "RiceRoundFloatNode" == e.comfyClass && 4 == e.widgets.length && (e.widgets[0].value = "数值", 
    e.widgets[1].value = 0, e.widgets[2].value = 0, e.widgets[3].value = 100));
}

function setupParameterNode(e) {
    const t = e.prototype.onAdded;
    e.prototype.onAdded = function() {
        t?.apply(this, arguments), adaptWidgetsToConnection(this);
    };
    const o = e.prototype.onAfterGraphConfigured;
    e.prototype.onAfterGraphConfigured = function() {
        o?.apply(this, arguments), adaptWidgetsToConnection(this);
    };
    const n = e.prototype.onConnectOutput;
    e.prototype.onConnectOutput = function(e, t, o, i, a) {
        if (!(o.widget || [ "STRING", "COMBO", "combo" ].includes(o.type) || o.type.includes("*"))) return !1;
        if (n) {
            return n.apply(this, arguments);
        }
        return !0;
    };
    const i = e.prototype.onConnectionsChange;
    e.prototype.onConnectionsChange = function(e, t, o, n, a) {
        return 2 != e || o || !this?.type || "RiceRoundAdvancedChoiceNode" != this.type && "RiceRoundSimpleChoiceNode" != this.type || (this.widgets[0].value = "Parameter"), 
        app.configuringGraph || adaptWidgetsToConnection(this), i?.apply(this, arguments);
    };
}

function generateUUID() {
    let e = "";
    for (let t = 0; t < 32; t++) {
        e += Math.floor(16 * Math.random()).toString(16);
    }
    return e;
}

function rebootAPI() {
    if ("electronAPI" in window) return window.electronAPI.restartApp(), !0;
    api.fetchApi("/manager/reboot");
}

app.registerExtension({
    name: "riceround.custom",
    setup() {
        initDialogLib();
    },
    async beforeRegisterNodeDef(e, t, o) {
        if ([ "RiceRoundAdvancedChoiceNode", "RiceRoundSimpleChoiceNode", "RiceRoundIntNode", "RiceRoundFloatNode" ].includes(t.name) && setupParameterNode(e), 
        "RiceRoundEncryptNode" == t.name) {
            const t = 400, o = 120, n = e.prototype.onNodeCreated;
            e.prototype.onNodeCreated = function() {
                const e = n ? n.apply(this) : void 0;
                return void 0 !== this.size?.[0] && (this.size[0] = t), void 0 !== this.size?.[1] && (this.size[1] = Math.max(o, this.size[1])), 
                e;
            }, e.prototype.onResize = function(e) {
                return void 0 !== e?.[0] && (e[0] = t), void 0 !== e?.[1] && (e[1] = Math.max(o, e[1])), 
                e;
            };
        }
    },
    loadedGraphNode: async e => {
        if (!e.title) {
            const t = e.type;
            if (t && t.includes("RiceRoundAdvancedChoiceNode")) {
                const e = t.match(/RiceRoundAdvancedChoiceNode_([^_]+)_/);
                if (!e) return;
                const o = e[1], n = localStorage.getItem("riceround_choice_dontshow");
                if (n && Number(n) > Date.now()) return;
                await loadMessageBox();
                const i = await Swal.fire({
                    title: "高级选择节点安装确认",
                    html: '\n                        <div>\n                            <p>检测到高级选择节点，是否需要安装相关组件？</p>\n                            <div style="text-align: left; margin-top: 1em;">\n                                <input type="checkbox" id="swal-restart-checkbox">\n                                <label for="swal-restart-checkbox">安装后重启服务</label>\n                            </div>\n                        </div>\n                    ',
                    icon: "question",
                    showCancelButton: !0,
                    confirmButtonText: "安装",
                    cancelButtonText: "不再提示",
                    heightAuto: !1,
                    backdrop: !0,
                    allowOutsideClick: !1,
                    customClass: {
                        container: "riceround-swal-top-container"
                    },
                    preConfirm: () => ({
                        needReboot: document.getElementById("swal-restart-checkbox").checked
                    })
                });
                if (i.dismiss === Swal.DismissReason.cancel) {
                    const e = Date.now() + 2592e5;
                    return void localStorage.setItem("riceround_choice_dontshow", e.toString());
                }
                if (i.isConfirmed) try {
                    if (!(await api.fetchApi("/riceround/install_choice_node", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            template_id: o,
                            need_reboot: i.value.needReboot
                        })
                    })).ok) throw new Error("Installation failed");
                    await Swal.fire({
                        title: "安装成功",
                        text: i.value.needReboot ? "组件已安装，服务即将重启" : "组件已安装完成",
                        icon: "success",
                        heightAuto: !1,
                        customClass: {
                            container: "riceround-swal-top-container"
                        }
                    });
                } catch (e) {
                    await Swal.fire({
                        title: "安装失败",
                        text: "组件安装过程中出现错误",
                        icon: "error",
                        heightAuto: !1,
                        customClass: {
                            container: "riceround-swal-top-container"
                        }
                    });
                }
            }
        }
    },
    nodeCreated(e, t) {
        if ("RiceRoundEncryptNode" == e.comfyClass && e.widgets && e.widgets.length > 0) {
            const t = window.document.title;
            if (t || (t = localStorage.getItem("Comfy.PreviousWorkflow")), t) {
                let o = t.replace(/[<>:"/\\|?*]/g, " ").replace(/^\s+|\s+$/g, "");
                for (let t = 0; t < e.widgets.length; t++) {
                    let n = e.widgets[t];
                    if ("project_name" == n.name && ("" == n.value || null == n.value || "my_project" == n.value)) {
                        n.value = o;
                        break;
                    }
                }
            }
            e.widgets.push({
                name: "generate_uuid",
                type: "button",
                label: "Generate UUID",
                callback: () => {
                    const t = generateUUID();
                    for (let o = 0; o < e.widgets.length; o++) {
                        let n = e.widgets[o];
                        if ("template_id" == n.name) {
                            n.value = t;
                            break;
                        }
                    }
                }
            });
            const o = document.getElementById(e.id);
            o && o.appendChild(button);
        }
    }
});