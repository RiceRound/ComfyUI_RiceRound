import { api as e } from "../../../scripts/api.js";

import { ComfyApp as t, app as o } from "../../../scripts/app.js";

const n = document.createElement("style");

n.textContent = "\n    .riceround-swal-top-container {\n        z-index: 99999 !important;\n    }\n", 
document.head.appendChild(n);

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

let i = !1;

async function s() {
    if (!i) {
        const e = "https://cdn.jsdelivr.net/npm/toastify-js", t = "https://cdn.jsdelivr.net/npm/toastify-js/src/toastify.min.css";
        await loadResource(e, t), i = !0;
    }
}

export async function showToast(e, t = "info", o = 3e3) {
    await s(), "info" == t ? Toastify({
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

let a = !1;

export async function loadMessageBox() {
    a || (await loadResource("https://cdn.jsdelivr.net/npm/sweetalert2@11", "https://cdn.jsdelivr.net/npm/@sweetalert2/theme-bootstrap-4/bootstrap-4.css"), 
    a = !0);
}

async function c(t, o) {
    await loadMessageBox();
    const n = {
        ...t,
        heightAuto: !1
    };
    try {
        const t = await Swal.fire(n);
        e.fetchApi("/riceround/message", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: `id=${o}&message=${t.isConfirmed ? "1" : "0"}`
        });
    } catch (t) {
        e.fetchApi("/riceround/message", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: `id=${o}&message=0`
        });
    }
    window.addEventListener("beforeunload", (function() {
        fetch("/riceround/message", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: `id=${o}&message=0`,
            keepalive: !0
        });
    }), {
        once: !0
    });
}

e.addEventListener("riceround_toast", (e => {
    showToast(e.detail.content, e.detail.type, e.detail.duration);
})), e.addEventListener("riceround_dialog", (e => {
    c(JSON.parse(e.detail.json_content), e.detail.id);
}));

let r = !1;

async function d(e, t, o = 5e3) {
    return new Promise(((n, i) => {
        const s = Date.now(), a = () => {
            Date.now() - s > o ? i(new Error(`Timeout waiting for ${t} to load`)) : e() ? n() : setTimeout(a, 50);
        };
        a();
    }));
}

export async function initDialogLib(e = !1) {
    if (!r) try {
        const e = "https://unpkg.com/vue@3/dist/vue.global.js";
        await loadResource(e, ""), await d((() => window.Vue), "vue");
        const t = "https://cdn.jsdelivr.net/npm/element-plus", o = "https://cdn.jsdelivr.net/npm/element-plus/dist/index.css";
        if (await loadResource(t, o), await d((() => window.ElementPlus), "element-plus"), 
        null == window.DialogLib) {
            const e = "riceround/static/dialog-lib.umd.cjs";
            await loadResource(e, ""), await d((() => window.DialogLib), "showLoginDialog");
        }
        r = !0;
    } catch (e) {
        throw e;
    }
}

async function l(t) {
    try {
        const o = {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(t)
        }, n = await e.fetchApi("/riceround/set_node_additional_info", o);
        await n.json();
    } catch (e) {}
}

function u(e, t, o, n) {
    e.type = t, e.value = o, e.options = n;
}

function p(e, t, o, n) {
    "customtext" === t && (t = "text");
    const i = n.options;
    var s = e.widgets[1].value;
    i?.values?.includes(s) || (s = n.value), "RiceRoundAdvancedChoiceNode" == e.comfyClass || "RiceRoundSimpleChoiceNode" == e.comfyClass ? u(e.widgets[1], t, s, i) : "RiceRoundIntNode" != e.comfyClass && "RiceRoundFloatNode" != e.comfyClass || 4 == e.widgets.length && (u(e.widgets[1], "number", s, i), 
    u(e.widgets[2], "number", i?.min ?? 0, i), u(e.widgets[3], "number", i?.max ?? 100, i));
}

function m(e, t, o, n) {
    if (e.outputs[0].type = o.type, "name" === e.widgets[0].label) {
        ([ "数值", "文本", "列表", "参数", "Parameter" ].includes(e.widgets[0].value) || "" == e.widgets[0].value) && (e.widgets[0].value = o.label ? o.label : o.name);
    }
    const i = o.widget?.name ? o.widget?.name : o.name, s = t.widgets.find((e => e.name === i));
    if (!s) return;
    p(e, s.origType ?? s.type, t, s);
}

e.addEventListener("riceround_login_dialog", (t => {
    const o = t.detail.client_key, n = t.detail.title;
    window.DialogLib.showLoginDialog({
        title: n,
        spyNetworkError: !0,
        mainKey: "riceround"
    }).then((t => {
        e.fetchApi("/riceround/auth_callback", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                token: t,
                client_key: o
            })
        }), showToast("登录成功");
    })).catch((e => {
        showToast("登录失败", "error");
    }));
})), e.addEventListener("riceround_show_workflow_payment_dialog", (e => {
    const t = e.detail.title ?? "支付", o = e.detail.template_id;
    o ? window.DialogLib.showWorkflowQRPaymentDialog({
        title: t,
        template_id: o
    }).then((({success: e, msg: t}) => {
        showToast(t, e ? "info" : "error");
    })).catch((e => {
        showToast("取消支付", "error");
    })) : showToast("模板ID不能为空", "error");
})), e.addEventListener("riceround_clear_user_info", (async e => {
    const t = e.detail.clear_key;
    "all" == t ? (localStorage.removeItem("Comfy.Settings.RiceRound.User.long_token"), 
    localStorage.removeItem("riceround_user_token"), o.ui.settings.setSettingValue("RiceRound.User.long_token", "")) : "long_token" == t ? (localStorage.removeItem("Comfy.Settings.RiceRound.User.long_token"), 
    o.ui.settings.setSettingValue("RiceRound.User.long_token", "")) : "user_token" == t && localStorage.removeItem("riceround_user_token");
})), e.addEventListener("execution_start", (async ({detail: e}) => {
    let t = "";
    const n = {};
    for (const e of o.graph.nodes) {
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
            const o = e.graph.links[e.outputs[0].links[0]];
            if (!o) continue;
            const i = e.graph.getNodeById(o.target_id);
            if (!i?.inputs || "RiceRoundDecryptNode" === i.comfyClass || "RiceRoundEncryptNode" === i.comfyClass) continue;
            const s = i.inputs[o.target_slot];
            if (!s || !i.widgets) continue;
            const a = s.widget?.name || s.name;
            if (!a) continue;
            const c = `${i.comfyClass}.${a}`;
            n[e.id] = {
                class_name: c,
                options_value: t,
                node_type: e.type
            };
        }
    }
    t && Object.keys(n).length > 0 && await l({
        choice_node_map: n,
        template_id: t
    });
}));

let g = null;

function h(e, t) {
    g && clearTimeout(g), g = setTimeout((() => {
        g = null;
        const o = t.graph.extra?.choice_node_map;
        if (e && e.widgets && 2 === e.widgets.length && o && o[e.id]) {
            const t = {
                values: o[e.id]
            };
            u(e.widgets[1], "combo", e.widgets[1].value, t);
        }
    }), 200);
}

function f(e) {
    if (!e.outputs || 0 === e.outputs.length) return;
    const t = e.outputs[0].links;
    if (t && 1 === t.length) {
        const n = e.graph.links[t[0]];
        if (!n) return;
        const i = e.graph.getNodeById(n.target_id);
        if (!i || !i.inputs) return;
        if ("RiceRoundDecryptNode" == i.comfyClass && "RiceRoundSimpleChoiceNode" == e.comfyClass) return void h(e, o);
        if ("RiceRoundEncryptNode" == i.comfyClass || "RiceRoundDecryptNode" == i.comfyClass) return;
        const s = i.inputs[n.target_slot];
        if (!s || void 0 === i.widgets) return;
        m(e, i, s, o);
    } else t && 0 !== t.length || ("RiceRoundAdvancedChoiceNode" == e.comfyClass || "RiceRoundSimpleChoiceNode" == e.comfyClass ? (e.widgets[0].value = "Parameter", 
    e.outputs[0].type = "*") : "RiceRoundIntNode" == e.comfyClass ? 4 == e.widgets.length && (e.widgets[0].value = "数值", 
    e.widgets[1].value = 0, e.widgets[2].value = 0, e.widgets[3].value = 100) : "RiceRoundFloatNode" == e.comfyClass && 4 == e.widgets.length && (e.widgets[0].value = "数值", 
    e.widgets[1].value = 0, e.widgets[2].value = 0, e.widgets[3].value = 100));
}

function w(e) {
    const t = e.prototype.onAdded;
    e.prototype.onAdded = function() {
        t?.apply(this, arguments), f(this);
    };
    const n = e.prototype.onAfterGraphConfigured;
    e.prototype.onAfterGraphConfigured = function() {
        n?.apply(this, arguments), f(this);
    };
    const i = e.prototype.onConnectOutput;
    e.prototype.onConnectOutput = function(e, t, o, n, s) {
        return !(!o.widget && !(o.type in [ "STRING", "COMBO", "combo" ])) && (!i || (result = i.apply(this, arguments), 
        result));
    };
    const s = e.prototype.onConnectionsChange;
    e.prototype.onConnectionsChange = function(e, t, n, i, a) {
        return 2 != e || n || !this?.type || "RiceRoundAdvancedChoiceNode" != this.type && "RiceRoundSimpleChoiceNode" != this.type || (this.widgets[0].value = "Parameter"), 
        o.configuringGraph || f(this), s?.apply(this, arguments);
    };
}

function y() {
    let e = "";
    for (let t = 0; t < 32; t++) {
        e += Math.floor(16 * Math.random()).toString(16);
    }
    return e;
}

function R() {
    if ("electronAPI" in window) return window.electronAPI.restartApp(), !0;
    e.fetchApi("/manager/reboot");
}

o.registerExtension({
    name: "riceround.custom",
    setup() {
        initDialogLib();
    },
    async beforeRegisterNodeDef(e, t, o) {
        if ([ "RiceRoundAdvancedChoiceNode", "RiceRoundSimpleChoiceNode", "RiceRoundIntNode", "RiceRoundFloatNode" ].includes(t.name) && w(e), 
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
    loadedGraphNode: async t => {
        if (!t.title) {
            const o = t.type;
            if (o && o.includes("RiceRoundAdvancedChoiceNode")) {
                const t = o.match(/RiceRoundAdvancedChoiceNode_([^_]+)_/);
                if (!t) return;
                const n = t[1];
                await loadMessageBox();
                const i = await Swal.fire({
                    title: "高级选择节点安装确认",
                    html: '\n                        <div>\n                            <p>检测到高级选择节点，是否需要安装相关组件？</p>\n                            <div style="text-align: left; margin-top: 1em;">\n                                <input type="checkbox" id="swal-restart-checkbox">\n                                <label for="swal-restart-checkbox">安装后重启服务</label>\n                            </div>\n                        </div>\n                    ',
                    icon: "question",
                    showCancelButton: !0,
                    confirmButtonText: "安装",
                    cancelButtonText: "取消",
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
                if (i.isConfirmed) try {
                    if (!(await e.fetchApi("/riceround/install_choice_node", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            template_id: n,
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
                    const t = y();
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