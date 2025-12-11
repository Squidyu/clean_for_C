<!--
Sync Impact Report:
- Version change: [TEMPLATE] → 1.0.0
- Modified principles: All placeholders replaced with concrete principles
- Added sections: Technical Constraints, Development Workflow
- Removed sections: None (template structure preserved)
- Templates requiring updates:
  ✅ constitution.md (this file)
  ⚠ plan-template.md (should reference safety-first principle)
  ⚠ spec-template.md (should align with module-based design)
  ⚠ tasks-template.md (should include safety validation tasks)
- Follow-up TODOs: None
-->

# Windows C 盘清理工具 Constitution

## Core Principles

### I. 安全第一（NON-NEGOTIABLE）
所有清理操作必须经过安全验证。系统关键文件必须受到白名单保护，禁止删除。高风险操作（如删除 hiberfil.sys）必须显示明确警告，并要求用户明确确认"我已知晓风险"。所有删除操作必须可追溯和可回滚。误删系统文件的风险必须通过白名单机制完全消除。

### II. 透明与可控
所有清理操作必须清晰展示：清理前显示可释放空间预测，清理后显示实际释放空间统计。用户必须能够查看文件明细，支持模块级和文件级的展开查看。所有操作必须支持选择性清理，用户可以选择清理哪些模块和文件。风险等级（低/中/高）必须明确标识，帮助用户做出明智决策。

### III. 模块化设计
清理功能必须按模块组织（系统垃圾、Windows 更新残留、浏览器缓存、第三方应用缓存、回收站、大文件、应用残留、休眠文件）。每个模块独立扫描、独立展示、独立清理。模块设计必须支持扩展，便于后续添加新的清理模块。模块化架构必须保证各模块之间的低耦合和高内聚。

### IV. 日志与可追溯性
所有清理操作必须记录到日志文件，包括：时间戳、清理模块、删除文件列表、失败项、是否清理 hiberfil.sys。日志必须支持查询和审计。关键操作（如禁用休眠）必须支持回滚功能（如恢复休眠功能）。日志格式必须结构化，便于后续分析和问题排查。

### V. 性能与用户体验
扫描操作必须在合理时间内完成（SSD 环境下 ≤ 30 秒）。清理过程必须提供实时反馈，包括进度条和已释放空间显示。扫描操作必须支持多线程处理，并允许用户取消长时间运行的操作。界面必须清晰直观，符合 Windows 用户的使用习惯。

### VI. 权限管理
需要管理员权限的操作必须通过 UAC 提升。权限检查必须在操作前进行，失败时给出明确提示。所有权限请求必须说明原因。权限管理必须遵循最小权限原则，仅在必要时请求提升权限。

## Technical Constraints

- **平台要求**：仅支持 Windows 操作系统（Windows 10 及以上版本）
- **权限要求**：部分功能需要管理员权限（UAC 提升），必须优雅处理权限不足的情况
- **系统命令依赖**：使用 `powercfg` 命令管理休眠功能（`powercfg -h off/on`、`powercfg /a`）
- **文件系统**：仅处理 C 盘，不涉及其他驱动器（D/E 盘等）
- **性能要求**：扫描操作支持多线程，支持取消操作，SSD 环境下扫描时间 ≤ 30 秒
- **安全要求**：必须维护系统关键路径白名单，禁止删除白名单中的文件和目录

## Development Workflow

- **测试要求**：所有清理模块必须包含单元测试和集成测试。高风险操作（如 hiberfil.sys 删除）必须包含完整的测试覆盖
- **代码审查**：所有代码变更必须经过审查，确保符合安全原则。安全相关的代码变更需要额外审查
- **文档要求**：所有公共 API 和关键功能必须包含文档注释。用户可见的功能必须包含使用说明
- **错误处理**：所有文件操作必须包含异常处理，失败时记录日志并继续执行其他操作。关键错误必须向用户明确提示
- **版本控制**：遵循语义化版本控制（MAJOR.MINOR.PATCH）。重大安全更新必须升级 MAJOR 版本

## Governance

本宪法是项目开发的最高指导原则，所有开发决策必须符合这些原则。修改宪法需要：
1. 文档化修改原因和影响分析
2. 获得项目负责人批准
3. 更新相关模板和文档（plan-template.md、spec-template.md、tasks-template.md）
4. 更新版本号（遵循语义化版本：MAJOR.MINOR.PATCH）
   - MAJOR: 向后不兼容的原则移除或重新定义
   - MINOR: 新增原则或重大扩展
   - PATCH: 澄清、措辞修正、非语义性改进

所有代码审查必须验证是否符合宪法原则。复杂性必须被充分论证。使用 `.specify/templates/` 中的模板进行规范驱动的开发。安全相关的代码变更必须经过额外的安全审查。

**Version**: 1.0.0 | **Ratified**: 2025-12-10 | **Last Amended**: 2025-12-10
