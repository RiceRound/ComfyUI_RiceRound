import { api as e } from "../../../scripts/api.js";

import { ComfyApp as t, app as o } from "../../../scripts/app.js";

import { showToast as n } from "./riceround.js";

const i = "riceround_user_token";

function r(e) {
    if ("string" != typeof e) return !1;
    if (e.length < 50) return !1;
    const t = e.split(".");
    if (3 !== t.length) return !1;
    const o = /^[A-Za-z0-9_-]+$/;
    return t.every((e => e.length > 0 && o.test(e)));
}

async function s(t) {
    t ? localStorage.setItem("RiceRound.Cloud.exclusive", t) : localStorage.removeItem("RiceRound.Cloud.exclusive");
    200 != (await e.fetchApi("/riceround/set_exclusive_user", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            exclusive_user: t
        })
    })).status && n("设置专属用户客户ID失败", "error");
}

o.registerExtension({
    name: "riceround.config",
    async setup() {
        o.ui.settings.addSetting({
            id: "RiceRound.User.logout",
            name: "登出当前用户",
            type: () => {
                const t = document.createElement("tr"), r = document.createElement("td"), s = document.createElement("input");
                return s.type = "button", s.value = "登出", s.style.borderRadius = "8px", s.style.padding = "8px 16px", 
                s.style.fontSize = "14px", s.style.cursor = "pointer", s.style.border = "1px solid #666", 
                s.style.backgroundColor = "#444", s.style.color = "#fff", s.onclick = async () => {
                    localStorage.removeItem("Comfy.Settings.RiceRound.User.long_token"), localStorage.removeItem(i), 
                    o.ui.settings.setSettingValue("RiceRound.User.long_token", ""), await e.fetchApi("/riceround/logout"), 
                    n("登出成功");
                }, r.appendChild(s), t.appendChild(r), t;
            }
        }), o.ui.settings.addSetting({
            id: "RiceRound.User.long_token",
            name: "设置长效token",
            type: "text",
            textType: "password",
            defaultValue: "",
            tooltip: "用于非本机授权登录情况，请勿泄露！提倡使用本机登录授权更安全！",
            onChange: async function(t) {
                r(t) && await e.fetchApi("/riceround/set_long_token", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        long_token: t
                    })
                });
            }
        }), o.ui.settings.addSetting({
            id: "RiceRound.Setting.wait-time",
            name: "任务排队等待时间(秒)",
            tooltip: "不建议设置太短，否则可能等不到运行结果就退出了",
            type: "slider",
            attrs: {
                min: 30,
                max: 7200,
                step: 10
            },
            defaultValue: 600,
            onChange: t => {
                e.fetchApi("/riceround/set_wait_time", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        wait_time: t
                    })
                });
            }
        }), o.ui.settings.addSetting({
            id: "RiceRound.Publish",
            name: "自动发布工作流",
            type: "boolean",
            defaultValue: !0,
            tooltip: "设置为true时，会自动发布工作流",
            onChange: function(t) {
                e.fetchApi("/riceround/set_auto_publish", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        auto_publish: t
                    })
                }), t || localStorage.setItem("RiceRound.Setting.auto_overwrite", t);
            }
        }), o.ui.settings.addSetting({
            id: "RiceRound.Publish.auto_overwrite",
            name: "自动覆盖更新同id工作流",
            type: "boolean",
            tooltip: "设置为true时，会自动覆盖已有的template_id的数据",
            onChange: function(t) {
                e.fetchApi("/riceround/set_auto_overwrite", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        auto_overwrite: t
                    })
                });
            }
        }), o.ui.settings.addSetting({
            id: "RiceRound.Cloud.run_client",
            name: "自启动云节点客户端",
            type: "boolean",
            defaultValue: !0,
            tooltip: "没有任何云节点客户运行的话，则该用户云节点无法运行",
            onChange: function(t) {
                e.fetchApi("/riceround/set_run_client", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        run_client: t
                    })
                });
            }
        }), o.ui.settings.addSetting({
            id: "RiceRound.Advanced.setting",
            name: "模型列表存放位置，手动清理或安装高级节点",
            type: () => {
                const t = document.createElement("tr"), o = document.createElement("td"), n = document.createElement("input");
                return n.type = "button", n.value = "打开文件夹", n.style.borderRadius = "8px", n.style.padding = "8px 16px", 
                n.style.fontSize = "14px", n.style.cursor = "pointer", n.style.border = "1px solid #666", 
                n.style.backgroundColor = "#444", n.style.color = "#fff", n.onmouseover = () => {
                    n.style.backgroundColor = "#555";
                }, n.onmouseout = () => {
                    n.style.backgroundColor = "#444";
                }, n.onclick = () => {
                    e.fetchApi("/riceround/open_selector_list_folder", {
                        method: "GET",
                        headers: {
                            "Content-Type": "application/json"
                        }
                    });
                }, o.appendChild(n), t.appendChild(o), t;
            }
        });
    }
});