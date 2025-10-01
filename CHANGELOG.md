# 📋 Mito-Forge 更新日志

## [1.0.0] - 2025-09-30

### 🎉 重大更新

#### ✨ 新功能
- **智能体状态管理**: 完整的智能体查看、重启和监控功能
- **系统诊断工具**: 内置环境检查和自动修复功能
- **跨平台支持**: 支持 Windows、Linux、macOS 多平台运行
- **LangGraph 集成**: 基于状态机的工作流编排系统

#### 🔧 修复问题
- **表格显示修复**: 解决 Rich 表格在窄终端中的截断问题
- **智能体系统修复**: 添加缺失的 `get_agents_status()` 和 `restart_agent()` 方法
- **CLI 格式优化**: 修复帮助文档格式，提升用户体验
- **编码兼容性**: 统一 UTF-8 编码，支持跨平台字符显示

#### 🚀 性能优化
- **显示性能**: 使用轻量级文本格式替代复杂表格渲染
- **启动速度**: 优化模块导入和初始化流程
- **内存使用**: 改进智能体资源管理

#### 📖 文档更新
- 更新 README.md 反映最新功能
- 新增 BUGFIX_LOG.md 记录修复历程
- 完善命令行使用示例

### 🔄 API 变更

#### 新增命令
```bash
# 智能体管理
python -m mito_forge agents --detailed
python -m mito_forge agents --restart <agent_name>

# 系统诊断
python -m mito_forge doctor --fix-issues
python -m mito_forge doctor --check-dependencies
```

#### 改进的命令
```bash
# 配置管理 - 新的显示格式
python -m mito_forge config

# 流水线 - 增强的参数支持
python -m mito_forge pipeline --reads data.fastq --kingdom animal
```

### 🐛 已知问题
- 模型 API 连接需要网络环境（已知网络问题，非代码问题）
- 部分生物信息学工具需要手动安装

### 📊 测试覆盖
- ✅ CLI 命令功能测试
- ✅ 智能体系统测试
- ✅ 跨平台兼容性测试
- ✅ 错误处理测试

---

## [0.2.0] - 2025-09-29

### 🔧 基础架构
- 初始 LangGraph 架构实现
- 多智能体系统框架
- 基础 CLI 命令结构

### 🚀 核心功能
- 流水线执行框架
- 配置管理系统
- 日志系统

---

## [0.1.0] - 2025-09-28

### 🎯 项目初始化
- 项目结构搭建
- 基础依赖配置
- 初始文档框架

---

## 🔮 未来计划

### v1.1.0 (计划中)
- [ ] 增强的错误恢复机制
- [ ] 更多生物信息学工具集成
- [ ] 性能监控和优化
- [ ] 扩展的配置选项

### v1.2.0 (计划中)
- [ ] Web 界面支持
- [ ] 分布式计算支持
- [ ] 高级分析功能
- [ ] 插件系统

---

**维护者**: Mito-Forge 开发团队  
**许可证**: MIT License  
**项目主页**: https://github.com/mito-forge/mito-forge