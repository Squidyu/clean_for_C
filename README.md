# Windows C 盘智能清理工具

一款面向 Windows 用户的安全、透明、清晰、可控的 C 盘清理工具，用于解决磁盘占满、系统卡顿、Windows Update 残留文件过多等问题。

## 功能特性

- **8 类模块化扫描**：系统垃圾、Windows 更新残留、浏览器缓存、第三方应用缓存、回收站、大文件、应用残留、休眠文件
- **安全第一**：白名单保护关键系统文件，明确风险提示
- **选择性清理**：用户可精确选择要清理的模块和文件
- **实时反馈**：扫描和清理过程显示进度和预计/实际释放空间
- **日志记录**：完整的清理历史记录，支持审计
- **休眠文件管理**：安全处理 hiberfil.sys，支持回滚
- **多版本支持**：智能适配 Windows 7-11 各版本特性

## 系统要求

- Windows 7、Windows 8、Windows 8.1、Windows 10 或 Windows 11
- Python 3.11+
- 管理员权限（某些操作需要）

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Squidyu/clean_for_C.git
cd clean_for_C
```

### 2. 创建虚拟环境

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行应用

```bash
python src/main.py
```

### 5. 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并查看覆盖率
pytest --cov=src

# 运行特定测试
pytest tests/unit/test_whitelist_service.py

# 测试多版本支持
python test_version_support.py
```

## 项目结构

```
clean_for_C/
├── src/                    # 源代码
│   ├── models/            # 数据模型
│   ├── modules/           # 扫描模块
│   ├── services/          # 业务逻辑服务
│   ├── ui/                # 用户界面
│   └── utils/             # 工具函数
├── tests/                 # 测试套件
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── fixtures/          # 测试数据
├── specs/                 # 规范文档
├── logs/                  # 应用程序日志
├── config/                # 配置文件
├── requirements.txt       # Python 依赖
└── pytest.ini            # 测试配置
```

## 核心模块

### 扫描模块 (modules/)

- **BaseScanner**: 扫描器基类，定义统一接口
- **SystemJunkScanner**: 扫描系统临时文件
- **WindowsUpdatesScanner**: 扫描 Windows 更新残留（支持多版本）
- **BrowserCacheScanner**: 扫描浏览器缓存
- **AppCacheScanner**: 扫描第三方应用缓存
- **RecycleBinScanner**: 扫描回收站文件
- **LargeFilesScanner**: 扫描大文件
- **AppRemnantsScanner**: 扫描应用残留
- **HibernationScanner**: 扫描休眠文件（版本感知）

### 服务层 (services/)

- **ScannerService**: 协调多模块并行扫描
- **CleanerService**: 执行文件清理操作
- **LogService**: 管理清理日志
- **PermissionService**: 处理 Windows 权限
- **WhitelistService**: 管理系统白名单（版本特定）

### 数据模型 (models/)

- **ScanResult**: 扫描结果
- **FileInfo**: 文件信息
- **ScanReport**: 扫描报告
- **CleaningOperation**: 清理操作
- **CleaningLog**: 清理日志
- **SystemWhitelist**: 系统白名单（版本感知）
- **HibernationFileInfo**: 休眠文件信息

## 安全特性

- **白名单保护**：维护关键系统路径的白名单，版本特定保护，禁止删除
- **权限检查**：在操作前检查管理员权限
- **风险提示**：高风险操作需要明确用户确认
- **操作日志**：所有清理操作都有完整日志记录
- **回滚支持**：关键操作（如禁用休眠）支持恢复
- **版本感知**：根据 Windows 版本调整保护策略和功能

## 开发指南

### 代码规范

- 使用 Python 3.11+ 特性
- 使用类型提示
- 遵循 PEP 8 编码规范
- 添加文档字符串

### 测试策略

- 单元测试覆盖核心逻辑
- 集成测试验证端到端流程
- 使用 pytest 框架
- 目标覆盖率：80%+

### 贡献流程

1. Fork 项目
2. 创建功能分支
3. 编写测试
4. 实现功能
5. 运行测试
6. 提交 PR

## 许可证

[![License](https://img.shields.io/badge/license-Apache%202-4EB1BA.svg)](https://www.apache.org/licenses/LICENSE-2.0.html)

## 联系方式

个人微信: x1297554122

## 打赏支持

如果您觉得这个项目对您有帮助，欢迎通过以下方式支持开发者：

<div align="center">

### 国内
![微信打赏](config/weichat_small.png)        ![支付宝打赏](config/alipay_small.jpg)
### PayPal
paypal.me/suqidxu
</div>

> 💝 **您的支持是开源项目持续发展的动力！**  
> 每一份打赏都会用于：
> - 🖥️ 服务器维护费用  
> - 🛠️ 开发工具更新  
> - ✨ 功能持续改进  
> - 📚 技术文档完善  
> - 🐛 Bug修复和用户支持  
> 
> 感谢您的支持！❤️

---

## 技术栈

- **语言**: Python 3.11+
- **GUI**: tkinter (内置)
- **Windows 集成**: pywin32
- **测试**: pytest
- **代码质量**: type hints, docstrings
- **版本控制**: Git
- **多版本支持**: Windows 7-11 兼容性

## 性能目标

- 扫描完成时间：≤ 30 秒 (SSD)
- 操作取消响应：≤ 2 秒
- 系统文件保护：100% 准确率
- 用户体验：直观易用

## 风险分析

| 风险类型 | 描述 | 应对措施 |
|----------|------|----------|
| 误删系统文件 | 删除关键文件导致系统损坏 | 白名单保护 + 版本特定保护 |
| 权限不足 | 操作失败 | 权限检查 + UAC 提升 |
| 休眠文件影响 | 删除后开机变慢 | 明确风险提示 + 回滚支持 |
| 扫描耗时 | 对 SSD 较长 | 多线程 + 取消支持 |
| 版本兼容性 | 不同 Windows 版本路径差异 | 版本检测 + 动态路径适配 |

## 多版本支持特性

本工具已针对不同 Windows 版本进行了专门优化：

### Windows 7
- 保护 NTLDR、bootmgr 等传统引导文件
- 清理 Windows Update 旧版本缓存
- 兼容 XP 模式相关文件

### Windows 8 / 8.1
- 处理 AppReadiness 目录缓存
- 清理 Windows Store 应用缓存
- 支持现代应用（Metro 应用）清理

### Windows 10
- 清理 WindowsApps 目录下未使用的应用
- 处理 Delivery Optimization 缓存
- 支持 Windows 10 特有的系统文件清理

### Windows 11
- 支持 Windows 11 新增的系统目录
- 清理新版 Microsoft Store 缓存
- 兼容 WSL（Windows Subsystem for Linux）相关文件

### 智能特性
- **自动版本检测**：启动时自动识别 Windows 版本
- **动态路径适配**：根据版本调整系统路径
- **差异化白名单**：为每个版本维护专门的保护列表
- **版本特定功能**：不同版本启用相应的清理功能
