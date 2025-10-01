# 模型配置指南

Mito-Forge 支持多种大语言模型提供者，包括 OpenAI、本地 Ollama、以及各种兼容 API。本指南将帮助您配置和管理模型。

## 快速开始

### 1. 查看可用配置

```bash
# 列出所有模型配置
mito-forge model list

# 查看预设配置
mito-forge model presets

# 诊断配置问题
mito-forge model doctor
```

### 2. 使用预设配置

```bash
# 从 OpenAI 预设创建配置
mito-forge model create-from-preset openai my-openai --api-key sk-xxx

# 从 Ollama 预设创建配置（无需 API 密钥）
mito-forge model create-from-preset ollama my-ollama

# 从智谱 AI 预设创建配置
mito-forge model create-from-preset zhipu my-zhipu --api-key xxx
```

### 3. 设置默认配置

```bash
# 设置默认模型
mito-forge model use my-openai

# 查看当前配置
mito-forge model current
```

## 支持的模型提供者

### OpenAI 官方 API

```bash
# 使用环境变量
export OPENAI_API_KEY="sk-your-api-key"
mito-forge model create-from-preset openai openai-gpt4 --model gpt-4o

# 或直接指定 API 密钥
mito-forge model add openai-custom \
  --provider-type openai \
  --model gpt-4o-mini \
  --api-key sk-your-key \
  --api-base https://api.openai.com/v1
```

### 本地 Ollama

```bash
# 确保 Ollama 服务运行在 localhost:11434
mito-forge model create-from-preset ollama local-qwen --model qwen2.5:7b

# 自定义 Ollama 地址
mito-forge model add ollama-remote \
  --provider-type ollama \
  --model llama3.1:8b \
  --api-base http://192.168.1.100:11434
```

### 国内模型服务商

#### 智谱 AI (GLM)

```bash
export ZHIPU_API_KEY="your-zhipu-key"
mito-forge model create-from-preset zhipu zhipu-glm4 --model glm-4
```

#### 月之暗面 (Kimi)

```bash
export MOONSHOT_API_KEY="your-moonshot-key"
mito-forge model create-from-preset moonshot kimi-8k --model moonshot-v1-8k
```

#### DeepSeek

```bash
export DEEPSEEK_API_KEY="your-deepseek-key"
mito-forge model create-from-preset deepseek deepseek-chat
```

### 自定义 OpenAI 兼容 API

```bash
# 添加自定义 API
mito-forge model add my-custom \
  --provider-type openai_compatible \
  --model gpt-3.5-turbo \
  --api-key your-key \
  --api-base http://your-api-server.com/v1 \
  --description "我的自定义 API"
```

## 配置管理

### 测试配置

```bash
# 测试指定配置
mito-forge model test openai-gpt4

# 测试所有配置
mito-forge model list  # 会显示每个配置的可用状态
```

### 更新配置

```bash
# 更新 API 密钥
mito-forge model update my-openai --api-key new-api-key

# 更新模型
mito-forge model update my-openai --model gpt-4o

# 更新 API 基础 URL
mito-forge model update my-custom --api-base https://new-api-server.com/v1
```

### 删除配置

```bash
mito-forge model remove old-config
```

## 环境变量配置

您可以使用环境变量来管理 API 密钥：

```bash
# OpenAI
export OPENAI_API_KEY="sk-your-openai-key"

# 智谱 AI
export ZHIPU_API_KEY="your-zhipu-key"

# 月之暗面
export MOONSHOT_API_KEY="your-moonshot-key"

# DeepSeek
export DEEPSEEK_API_KEY="your-deepseek-key"

# 自定义
export CUSTOM_API_KEY="your-custom-key"
```

配置文件中可以使用 `${ENV_VAR}` 语法引用环境变量：

```yaml
my-profile:
  provider_type: openai
  model: gpt-4o-mini
  api_key: ${OPENAI_API_KEY}
  api_base: https://api.openai.com/v1
```

## 配置文件位置

配置文件存储在用户主目录下：

- **Windows**: `C:\Users\{username}\.mito-forge\`
- **Linux/macOS**: `~/.mito-forge/`

主要文件：
- `model_config.yaml`: 主配置文件
- `model_profiles.yaml`: 模型配置文件

## 导入导出配置

```bash
# 导出配置
mito-forge model export my-config.yaml

# 导入配置
mito-forge model import-config my-config.yaml
```

## 故障排除

### 常见问题

1. **API 密钥错误**
   ```bash
   mito-forge model doctor  # 检查环境变量
   mito-forge model test profile-name  # 测试特定配置
   ```

2. **Ollama 连接失败**
   ```bash
   # 检查 Ollama 服务状态
   curl http://localhost:11434/api/tags
   
   # 启动 Ollama 服务
   ollama serve
   ```

3. **网络连接问题**
   ```bash
   # 测试 API 连接
   curl -H "Authorization: Bearer your-api-key" \
        https://api.openai.com/v1/models
   ```

### 调试模式

设置环境变量启用详细日志：

```bash
export MITO_FORGE_LOG_LEVEL=DEBUG
mito-forge model test your-profile
```

## 最佳实践

1. **安全性**
   - 使用环境变量存储 API 密钥
   - 不要在配置文件中硬编码密钥
   - 定期轮换 API 密钥

2. **性能优化**
   - 本地模型优先：设置 Ollama 作为主要选择
   - 云端模型作为备用：配置自动回退
   - 根据任务选择合适的模型大小

3. **成本控制**
   - 使用较小的模型进行测试
   - 设置合理的 `max_tokens` 限制
   - 监控 API 使用量

## 示例配置文件

完整的 `model_profiles.yaml` 示例：

```yaml
openai-gpt4:
  provider_type: openai
  model: gpt-4o
  api_key: ${OPENAI_API_KEY}
  api_base: https://api.openai.com/v1
  description: OpenAI GPT-4

ollama-qwen:
  provider_type: ollama
  model: qwen2.5:7b
  api_base: http://localhost:11434
  description: 本地 Qwen 模型

zhipu-glm4:
  provider_type: zhipu
  model: glm-4
  api_key: ${ZHIPU_API_KEY}
  description: 智谱 GLM-4

custom-api:
  provider_type: openai_compatible
  model: gpt-3.5-turbo
  api_key: ${CUSTOM_API_KEY}
  api_base: https://my-api-server.com/v1
  description: 自定义 API 服务
```

对应的 `model_config.yaml`：

```yaml
default_profile: ollama-qwen
fallback_profiles:
  - zhipu-glm4
  - openai-gpt4
auto_fallback: true
```

这样配置后，系统会优先使用本地 Ollama，如果不可用则自动切换到智谱 AI，最后回退到 OpenAI。