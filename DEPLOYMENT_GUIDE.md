# Streamlit Cloud 部署完整指南

## 📦 必需文件清单

### ✅ 核心文件（必须包含在 Git 仓库中）

```
your-project/
├── app_cloud.py                          # 主应用（云端部署版）
├── requirements.txt                      # Python 依赖包
├── .streamlit/
│   └── config.toml                       # Streamlit 配置
├── model/
│   ├── README.md                         # 模型目录说明
│   └── ipso_bp_ensemble_model.pkl        # ⚠️ 训练好的模型文件（必需！）
└── training_scripts/
    ├── ipso_bp_slope_stability.py        # 原始训练脚本
    └── ipso_bp_slope_stability_fixed.py  # 修复版训练脚本（无特殊字符）
```

### 📋 文件说明

| 文件 | 用途 | 是否必须 |
|------|------|----------|
| `app_cloud.py` | Streamlit 主应用 | ✅ 必须 |
| `requirements.txt` | 依赖包列表 | ✅ 必须 |
| `.streamlit/config.toml` | Streamlit 配置 | ✅ 推荐 |
| `model/*.pkl` | 训练好的模型 | ✅ **必须** |
| `training_scripts/*.py` | 训练脚本 | ✅ 必须 |

---

## 🚀 部署步骤（5分钟搞定）

### **第1步：准备 GitHub 仓库**

1. 在 GitHub 创建新仓库（Public 或 Private）
2. 将所有必需文件上传到仓库根目录
3. **重要**: 确保模型文件已上传到 `model/` 目录

```bash
# 本地操作示例
git init
git add app_cloud.py requirements.txt .streamlit/ model/ training_scripts/
git commit -m "Initial deployment package"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### **第2步：注册 Streamlit Cloud**

1. 访问 [https://share.streamlit.io](https://share.streamlit.io)
2. 使用 GitHub 账号登录（推荐）或邮箱注册
3. 点击 "Deploy an app" 或 "New app"

### **第3步：配置应用**

在部署配置页面填写：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **Repository** | `YOUR_USERNAME/YOUR_REPO` | 你的 GitHub 仓库 |
| **Branch** | `main` | 主分支（或 master） |
| **Main file path** | `app_cloud.py` | 主应用文件路径 |
| **App title** (可选) | `边坡稳定性预测系统` | 应用标题 |

### **第4步：高级设置（可选但推荐）**

点击 "Advanced settings"：

#### **Python 版本**
- 选择: `3.10` 或 `3.11`
- 推荐使用 Python 3.10+ 以获得最佳兼容性

#### **Secrets（敏感信息）**
如果需要，可以添加环境变量：
- 通常本应用不需要额外 secrets

#### **硬件资源**
- **Memory**: 默认即可（模型约需 200-500MB RAM）
- **CPU**: 默认即可

### **第5步：部署**

1. 点击 **"Deploy"** 按钮
2. 等待构建完成（通常 2-5 分钟）
3. 部署成功后会显示应用 URL，格式为：
   ```
   https://YOUR_USERNAME-app_name.streamlit.app
   ```

---

## 🔧 常见问题排查

### ❌ 问题1: 模型文件未找到
**错误信息**: `📂 模型文件未找到`

**解决方案**:
```bash
# 1. 检查 model/ 目录是否存在 .pkl 文件
ls -la model/

# 2. 如果没有，从本地复制模型文件
cp /path/to/local/model/ipso_bp_ensemble_model.pkl model/

# 3. 提交并推送
git add model/ipso_bp_ensemble_model.pkl
git commit -m "Add model file"
git push origin main
```

### ❌ 问题2: 依赖安装失败
**错误信息**: `ModuleNotFoundError: No module named 'xxx'`

**解决方案**:
1. 检查 `requirements.txt` 是否完整
2. 确保版本号正确
3. 查看 Streamlit Cloud 的构建日志获取详细错误

### ❌ 问题3: 编码错误（Windows 特殊字符）
**错误信息**: `'gbk' codec can't encode character '\u2713'`

**解决方案**:
1. 使用修复版训练脚本重新生成模型：
   ```bash
   python training_scripts/ipso_bp_slope_stability_fixed.py
   ```
2. 替换 `model/` 目录下的 `.pkl` 文件
3. 重新部署

### ❌ 问题4: 内存不足
**错误信息**: `MemoryError` 或应用崩溃

**解决方案**:
- 模型文件过大时可能需要升级 Streamlit Cloud 计划
- 或优化模型大小（减少基模型数量）

---

## 💡 最佳实践

### 1️⃣ **版本控制**
```bash
# 为不同版本的模型打标签
git tag -a v1.0.0 -m "First stable release"
git push origin v1.0.0
```

### 2️⃣ **自动重新部署**
Streamlit Cloud 会自动检测 GitHub 更新并重新部署：
- 推送到 `main` 分支 → 自动触发重新部署
- 无需手动操作！

### 3️⃣ **监控和日志**
- 访问应用管理页面查看运行日志
- 监控资源使用情况
- 设置错误告警（可选）

### 4️⃣ **性能优化**
- 使用 `@st.cache_resource` 缓存模型加载
- 避免在每次交互时重复计算
- 合理使用 `st.session_state` 管理状态

---

## 📊 成本估算

### Streamlit Cloud 免费版限制
| 项目 | 免费额度 | 说明 |
|------|---------|------|
| **应用数量** | 3 个 Public 应用 | Private 需付费 |
| **内存** | 512 MB | 本应用足够 |
| **CPU** | 共享 CPU | 够用 |
| **每月运行时间** | 无限制 | - |

**结论**: 本应用完全可以在免费版上运行！💰

---

## 🔐 安全注意事项

### ✅ 应该做的
- 定期更新依赖包版本
- 不要在代码中硬编码敏感信息
- 使用 HTTPS 访问

### ❌ 不应该做的
- 不要将 API Key、密码等提交到 Git
- 不要在生产环境开启调试模式
- 不要暴露内部服务器信息

---

## 🎯 下一步

部署成功后，你可以：

1. **分享链接**: 将应用 URL 发给同事或客户
2. **自定义域名**: 在设置中绑定自定义域名（需付费计划）
3. **添加认证**: 实现用户登录功能（需自行开发）
4. **监控分析**: 集成 Google Analytics 等工具

---

## 📞 技术支持

如遇问题，请检查：

1. ✅ [Streamlit Cloud 文档](https://docs.streamlit.io/streamlit-community-cloud)
2. ✅ [GitHub Issues](https://github.com/streamlit/streamlit/issues)
3. ✅ [Stack Overflow](https://stackoverflow.com/questions/tagged/streamlit)

---

**祝部署顺利！🚀**

*最后更新: 2026-05-10*
