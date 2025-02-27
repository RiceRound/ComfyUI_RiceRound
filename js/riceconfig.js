import { api } from "../../../scripts/api.js";

import { ComfyApp, app } from "../../../scripts/app.js";

import { showToast } from "./riceround.js";

const UserTokenKey = "riceround_user_token";

function isValidJWTFormat(e) {
    if ("string" != typeof e) return !1;
    if (e.length < 50) return !1;
    const t = e.split(".");
    if (3 !== t.length) return !1;
    const n = /^[A-Za-z0-9_-]+$/;
    return t.every((e => e.length > 0 && n.test(e)));
}

async function exportTomlMessageBox(e) {
    const t = document.createElement("div");
    document.body.appendChild(t);
    const {createApp: n, ref: o} = Vue, i = n({
        template: '\n            <el-dialog\n                v-model="dialogVisible"\n                :title="title"\n                width="500px"                \n                center\n                @close="handleClose"\n            >       \n                <el-form :model="form" label-position="top">\n                    <el-form-item label="请输入机器码">\n                        <el-input\n                            v-model="form.secretToken"\n                            type="textarea"\n                            :rows="4"\n                            placeholder="请输入从官网获取的机器码"\n                            :disabled="loading"\n                        />\n                    </el-form-item>\n                </el-form>\n                <template #footer>\n                    <div class="dialog-footer" style="display: flex; justify-content: flex-end; gap: 12px;">\n                        <el-button                            \n                            @click="handleGenerate"\n                            :loading="loading"\n                        >\n                            生成配置文件\n                        </el-button>\n                        <el-button\n                            type="primary"\n                            @click="openHelp"\n                        >\n                            帮助文档\n                        </el-button>\n                    </div>\n                </template>\n            </el-dialog>\n        ',
        setup() {
            const e = o(!0), n = o(!1), l = o({
                secretToken: ""
            }), a = () => {
                document.body.removeChild(t), i.unmount();
            };
            return {
                dialogVisible: e,
                loading: n,
                form: l,
                handleClose: a,
                handleGenerate: async () => {
                    if (l.value.secretToken) {
                        n.value = !0;
                        try {
                            const e = await api.fetchApi("/riceround/export_toml", {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json"
                                },
                                body: JSON.stringify({
                                    secret_token: l.value.secretToken
                                })
                            });
                            if (e.ok) {
                                const t = await e.blob(), n = window.URL.createObjectURL(t), o = document.createElement("a");
                                o.href = n, o.download = "client.toml", document.body.appendChild(o), o.click(), 
                                window.URL.revokeObjectURL(n), document.body.removeChild(o), ElementPlus.ElMessage.success("配置文件生成成功"), 
                                a();
                            } else {
                                const t = await e.json();
                                ElementPlus.ElMessage.error(t.message || "生成配置文件失败");
                            }
                        } catch (e) {
                            ElementPlus.ElMessage.error("生成配置文件失败");
                        } finally {
                            n.value = !1;
                        }
                    } else ElementPlus.ElMessage.warning("请输入机器码");
                },
                openHelp: () => {
                    window.open("https://help.riceround.online/", "_blank");
                }
            };
        }
    });
    i.use(ElementPlus), i.mount(t);
}

async function set_exclusive_user(e) {
    e ? localStorage.setItem("RiceRound.Cloud.exclusive", e) : localStorage.removeItem("RiceRound.Cloud.exclusive");
    200 != (await api.fetchApi("/riceround/set_exclusive_user", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            exclusive_user: e
        })
    })).status && showToast("设置专属用户客户ID失败", "error");
}

app.registerExtension({
    name: "riceround.config",
    async setup() {
        app.ui.settings.addSetting({
            id: "RiceRound.User.logout",
            name: "登出当前用户",
            type: () => {
                const e = document.createElement("tr"), t = document.createElement("td"), n = document.createElement("input");
                return n.type = "button", n.value = "登出", n.style.borderRadius = "8px", n.style.padding = "8px 16px", 
                n.style.fontSize = "14px", n.style.cursor = "pointer", n.style.border = "1px solid #666", 
                n.style.backgroundColor = "#444", n.style.color = "#fff", n.onclick = async () => {
                    localStorage.removeItem("Comfy.Settings.RiceRound.User.long_token"), localStorage.removeItem(UserTokenKey), 
                    app.ui.settings.setSettingValue("RiceRound.User.long_token", ""), await api.fetchApi("/riceround/logout"), 
                    showToast("登出成功");
                }, t.appendChild(n), e.appendChild(t), e;
            }
        }), app.ui.settings.addSetting({
            id: "RiceRound.User.long_token",
            name: "设置长效token",
            type: "text",
            textType: "password",
            defaultValue: "",
            tooltip: "用于非本机授权登录情况，请勿泄露！提倡使用本机登录授权更安全！",
            onChange: async function(e) {
                isValidJWTFormat(e) && await api.fetchApi("/riceround/set_long_token", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        long_token: e
                    })
                });
            }
        }), app.ui.settings.addSetting({
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
            onChange: e => {
                api.fetchApi("/riceround/set_wait_time", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        wait_time: e
                    })
                });
            }
        }), app.ui.settings.addSetting({
            id: "RiceRound.Publish",
            name: "自动发布工作流",
            type: "boolean",
            defaultValue: !0,
            tooltip: "设置为true时，会自动发布工作流",
            onChange: function(e) {
                api.fetchApi("/riceround/set_auto_publish", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        auto_publish: e
                    })
                }), e || localStorage.setItem("RiceRound.Setting.auto_overwrite", e);
            }
        }), app.ui.settings.addSetting({
            id: "RiceRound.Cloud.export",
            name: "生成云机器配置",
            type: () => {
                const e = document.createElement("tr"), t = document.createElement("td"), n = document.createElement("input");
                return n.type = "button", n.value = "导出", n.style.borderRadius = "8px", n.style.padding = "8px 16px", 
                n.style.fontSize = "14px", n.style.cursor = "pointer", n.style.border = "1px solid #666", 
                n.style.backgroundColor = "#444", n.style.color = "#fff", n.onclick = async () => {
                    exportTomlMessageBox("生成云机器配置");
                }, t.appendChild(n), e.appendChild(t), e;
            }
        }), app.ui.settings.addSetting({
            id: "RiceRound.Advanced.setting",
            name: "模型列表存放位置，手动清理或安装高级节点",
            type: () => {
                const e = document.createElement("tr"), t = document.createElement("td"), n = document.createElement("input");
                return n.type = "button", n.value = "打开文件夹", n.style.borderRadius = "8px", n.style.padding = "8px 16px", 
                n.style.fontSize = "14px", n.style.cursor = "pointer", n.style.border = "1px solid #666", 
                n.style.backgroundColor = "#444", n.style.color = "#fff", n.onmouseover = () => {
                    n.style.backgroundColor = "#555";
                }, n.onmouseout = () => {
                    n.style.backgroundColor = "#444";
                }, n.onclick = () => {
                    api.fetchApi("/riceround/open_folder?id=2", {
                        method: "GET",
                        headers: {
                            "Content-Type": "application/json"
                        }
                    });
                }, t.appendChild(n), e.appendChild(t), e;
            }
        });
    }
});