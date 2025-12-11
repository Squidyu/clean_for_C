# Windows 多版本支持

本文档说明了 Windows C 盘清理工具对 Windows 7、8、8.1、10 和 11 的支持情况。

## 支持的版本

| 版本 | 支持级别 | 构建号范围 | 主要特性 |
|------|----------|------------|----------|
| Windows 7 | 基础支持 | 6.1.7600+ | 休眠文件、基础更新清理 |
| Windows 8 | 增强支持 | 6.2.9200+ | 混合启动、Windows Store |
| Windows 8.1 | 增强支持 | 6.3.9600+ | 改进的混合启动 |
| Windows 10 | 完整支持 | 10.0.10240+ | UWP 应用、WSL、完整清理 |
| Windows 11 | 完整支持 | 10.0.22000+ | DirectStorage、增强保护 |

## 新增功能

### 1. 智能系统检测 (`utils/system_info.py`)

- 自动检测 Windows 版本和构建号
- 识别系统架构（32/64位）
- 检测版本特定功能支持

### 2. 版本特定路径配置 (`SystemPaths` 类)

根据 Windows 版本提供不同的：
- 系统保护路径
- 临时目录位置
- 更新缓存目录

### 3. 增强的白名单系统

- 版本特定的保护路径
- 动态配置保护规则
- 回退机制确保系统安全

### 4. 智能休眠文件处理

- 根据系统版本调整清理策略
- 版本特定的警告和提示
- 优雅的禁用和恢复功能

## 版本差异说明

### Windows 7

**支持的功能：**
- 休眠文件清理（`hiberfil.sys`）
- Service Pack 卸载文件夹清理
- Windows Update 缓存清理
- 基础临时文件清理

**注意事项：**
- 不支持快速启动（Windows 8 引入）
- 没有 Windows Store 应用
- 较简单的系统结构

### Windows 8 / 8.1

**新增功能：**
- 混合启动（快速启动）
- Windows Store 应用
- AppReadiness 缓存

**处理差异：**
- 休眠文件与快速启动关联
- 需要额外保护 Store 应用
- 新增 AppReadiness 目录

### Windows 10

**新增功能：**
- UWP (Universal Windows Platform) 应用
- WSL (Windows Subsystem for Linux)
- 优化的 Windows Update
- Component Store (WinSxS) 管理

**处理差异：**
- 保护 SystemApps 目录
- WSL 相关路径保护
- 更复杂的更新清理机制

### Windows 11

**新增功能：**
- DirectStorage 支持
- 增强的 UI 系统
- 改进的驱动程序管理

**处理差异：**
- 保护 SystemResources 目录
- 驱动程序存储增强保护
- 64位强制要求

## 配置文件

### `config/windows_versions.json`

包含所有 Windows 版本的详细配置：
- 功能支持矩阵
- 路径配置
- 兼容性信息
- 版本特定说明

## 使用方法

### 自动检测

程序启动时自动检测 Windows 版本：

```python
from utils.system_info import system_info

version = system_info.get_windows_version()
print(f"当前系统: {version.value}")
```

### 版本特定操作

```python
# 检查功能支持
if system_info.supports_feature('hibernation'):
    # 执行休眠相关操作
    pass

# 获取版本特定路径
from utils.system_info import SystemPaths
temp_dirs = SystemPaths.get_temp_directories(version)
```

### 清理策略调整

清理操作会根据检测到的 Windows 版本自动调整：
- 保护不同的系统路径
- 使用版本特定的清理算法
- 提供相关的警告信息

## 测试

运行版本支持测试：

```bash
python test_version_support.py
```

该测试会验证：
- 系统版本检测准确性
- 路径配置正确性
- 功能支持检测
- 白名单配置
- 命令行工具兼容性

## 兼容性注意事项

### 命令行工具

所有版本都使用标准的 `powercfg` 命令：
- `powercfg /h off` - 禁用休眠
- `powercfg /h on` - 启用休眠
- `powercfg /a` - 检查睡眠状态

### 权限要求

- Windows 7/8: 需要管理员权限进行系统级操作
- Windows 10/11: UAC 严格控制某些操作

### 特殊情况

1. **系统升级后**：可能需要重新扫描以识别新路径
2. **多系统启动**：每个系统有独立的配置
3. **企业版**：可能有额外的组策略限制

## 更新日志

### v2.0.0
- 新增 Windows 版本自动检测
- 实现版本特定路径配置
- 增强系统保护机制
- 优化休眠文件处理逻辑
- 添加 Windows 11 支持

### v1.0.0
- 基础 Windows 10 支持
- 标准系统清理功能

## 故障排除

### 版本检测失败

如果版本检测失败，程序会：
1. 回退到基础保护模式
2. 使用通用路径配置
3. 显示警告信息

### 路径不存在

某些版本特定的路径可能不存在：
- 正常情况，不影响其他功能
- 程序会自动跳过不存在的路径
- 可以在配置中禁用特定检查

### 权限问题

确保：
- 以管理员身份运行
- UAC 设置正确
- 防病毒软件不阻止操作

## 贡献

如需添加新的 Windows 版本支持：
1. 更新 `system_info.py` 中的版本检测逻辑
2. 在 `windows_versions.json` 中添加配置
3. 更新测试用例
4. 测试兼容性

## 许可证

本多版本支持功能遵循项目主许可证。