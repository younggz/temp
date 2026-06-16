# LLM Agent Skills 适配机制 - 演示系统说明文档

## 📌 项目概述

本系统是一个完整的 **LLM Agent Skills 适配机制** 演示项目，解决了以下核心问题：

> **如何让技能适配不同的 Agent 和大模型？如何让用户知道技能是否适合当前的 Agent 和模型？**

### 核心问题

1. **能力差异**：不同模型的能力不一样（上下文长度、推理能力、代码生成等）
2. **机制差异**：不同 Agent 支持的机制不同（hooks、长时任务、记忆等）
3. **适配问题**：如何避免用户将技能用在不适合的 Agent 和模型中
4. **解决方案**：技能适配层、替代技能路由、技能编译层

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层                               │
│                  (Web 演示页面)                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Django 后端层                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Skill Adapter│  │ Skill Router │  │ Skill Compiler   │   │
│  │  (适配层)    │  │  (路由层)    │  │  (编译层)        │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   能力定义层                                  │
│  ┌─────────────────────┐  ┌───────────────────────────┐    │
│  │ Agent Capability     │  │ Model Capability          │    │
│  │ (Agent能力画像)      │  │ (模型能力画像)            │    │
│  └─────────────────────┘  └───────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 核心模块说明

### 1. 技能适配层 (`nlp/skill_adapter.py`)

**功能**：定义技能的元数据和能力要求

#### 核心类

- **`SkillAdapter`**：技能适配器，管理所有技能的注册和兼容性检查
- **`SkillMetadata`**：技能元数据（名称、描述、版本、分类、依赖等）
- **`SkillRequirement`**：技能能力要求（Agent能力、模型能力、上下文长度等）

#### 关键方法

```python
# 注册技能
adapter.register_skill(
    name='advanced_search',
    func=search_function,
    description='高级搜索技能',
    required_agent_capabilities={AgentCapability.MEMORY},
    required_model_capabilities={ModelCapability.REASONING},
    min_context_length=8192,
    alternatives=['basic_search']  # 替代技能
)

# 检查兼容性
result = adapter.check_skill_compatibility(
    skill_name='advanced_search',
    agent_capabilities=agent_caps,
    model_capabilities=model_caps,
    context_length=8192
)
# 返回: {'compatible': bool, 'score': float, 'warnings': [...], ...}
```

#### 能力类型枚举

**Agent 能力**：
- `HOOKS`：支持钩子机制
- `LONG_TASK`：支持长时任务
- `MEMORY`：支持记忆
- `MULTI_TURN`：支持多轮对话
- `TOOL_USE`：支持工具调用
- `CODE_EXEC`：支持代码执行
- `WEB_SEARCH`：支持网络搜索
- `FILE_IO`：支持文件读写

**模型能力**：
- `CONTEXT_LENGTH`：上下文长度
- `REASONING`：推理能力
- `CODE_GENERATION`：代码生成
- `MULTI_LANGUAGE`：多语言支持
- `VISION`：视觉理解
- `FUNCTION_CALLING`：函数调用

---

### 2. 技能路由层 (`nlp/skill_router.py`)

**功能**：当主技能不兼容时，智能路由到替代技能

#### 核心类

- **`SkillRouter`**：技能路由器，负责技能调度的智能决策

#### 路由流程

```
用户请求技能A
    ↓
检查技能A兼容性
    ↓
如果兼容 → 执行技能A
    ↓
如果不兼容 → 查找替代技能列表
    ↓
对替代技能进行兼容性排序
    ↓
选择最优替代技能
    ↓
记录路由历史
```

#### 关键方法

```python
router = SkillRouter(skill_adapter)

# 路由技能
result = router.route_skill(
    skill_name='advanced_search',
    agent_capabilities=agent_caps,
    model_capabilities=model_caps,
    context_length=4096
)
# 返回: {
#     'original_skill': 'advanced_search',
#     'routed_skill': 'basic_search',
#     'was_rerouted': True,
#     'reason': '原技能需要推理能力，当前模型不支持',
#     'alternatives': [...]
# }
```

---

### 3. 技能编译器 (`nlp/skill_compiler.py`)

**功能**：编译和验证技能适配性，生成可执行的技能配置

#### 核心类

- **`SkillCompiler`**：技能编译器，负责完整的编译流程

#### 编译流程

```
1. 检查缓存
2. 验证技能存在性
3. 检查能力兼容性
4. 解析依赖关系
5. 路由到最优技能
6. 生成执行计划
7. 缓存结果
```

#### 关键方法

```python
compiler = SkillCompiler(adapter, router)

# 编译技能
result = compiler.compile_skill(
    skill_name='long_task_analysis',
    agent_capabilities=agent_caps,
    model_capabilities=model_caps,
    context_length=16384
)

# 生成编译报告
report = compiler.get_compilation_report(result)
```

---

### 4. Agent 能力描述模块 (`nlp/agent_capability.py`)

**功能**：定义不同类型 Agent 和大模型的能力特征

#### 预定义的 Agent 类型

| 类型 | 能力 | 最大上下文 | 钩子 | 长时任务 | 记忆 |
|------|------|-----------|------|---------|------|
| **基础Agent** | 工具调用 | 4096 | ❌ | ❌ | ❌ |
| **标准Agent** | 工具调用、多轮、记忆 | 8192 | ❌ | ❌ | ✅ |
| **高级Agent** | 完整能力 | 16384 | ✅ | ✅ | ✅ |
| **企业级Agent** | 所有能力 | 32768 | ✅ | ✅ | ✅ |

#### 预定义的模型类型

| 类型 | 能力 | 上下文长度 |
|------|------|-----------|
| **小型模型** | 上下文长度 | 4096 |
| **中型模型** | 上下文、推理、多语言、函数调用 | 8192 |
| **大型模型** | +代码生成 | 16384 |
| **超大型模型** | +视觉理解 | 32768 |

---

## 🚀 使用方法

### 1. 启动系统

```bash
# 确保已安装依赖
pip install django jieba python-docx

# 初始化数据库（如果还没初始化）
python manage.py migrate

# 启动服务
python manage.py runserver
```

### 2. 访问演示页面

访问：http://127.0.0.1:8000/skill_demo/

### 3. 演示功能

#### 3.1 技能库浏览
- 查看所有已注册的技能
- 查看每个技能的能力要求
- 查看技能的替代方案

#### 3.2 Agent/模型能力对比
- 对比不同类型 Agent 的能力差异
- 对比不同模型的 capabilities
- 理解能力差异对技能选择的影响

#### 3.3 兼容性检查
- 选择技能、Agent、模型
- 实时检查兼容性
- 查看兼容性评分和警告
- 获取优化建议

#### 3.4 技能编译
- 编译技能配置
- 查看编译报告
- 查看执行计划
- 了解路由决策

---

## 💡 解决方案总结

本系统提供了 **三层防护机制** 来解决技能适配问题：

### 第一层：技能适配层（Skill Adapter Layer）

**作用**：明确定义技能的能力要求

- 技能注册时声明所需的 Agent 和模型能力
- 提供兼容性检查接口
- 用户可以在使用前检查技能是否适合当前环境

**解决的问题**：
- ✅ 让用户知道技能需要什么能力
- ✅ 避免盲目使用不兼容的技能

### 第二层：技能路由层（Skill Router）

**作用**：自动选择最合适的技能

- 当主技能不兼容时，自动查找替代技能
- 对替代技能进行兼容性排序
- 记录路由历史，便于调试

**解决的问题**：
- ✅ 自动降级到兼容的替代技能
- ✅ 保证任务能够继续执行
- ✅ 提供透明的路由决策

### 第三层：技能编译层（Skill Compiler）

**作用**：编译和验证完整的技能配置

- 解析技能依赖关系
- 生成优化的执行计划
- 提供详细的编译报告

**解决的问题**：
- ✅ 提前发现配置问题
- ✅ 生成可执行的计划
- ✅ 提供调试信息

---

## 📊 示例场景

### 场景1：基础 Agent 使用高级技能

```
技能：long_task_analysis（需要长时任务、代码执行能力）
Agent：基础Agent（只有工具调用能力）
模型：小型模型（4096上下文）

结果：
❌ 不兼容
⚠️  Agent缺少能力: long_task, code_exec
⚠️  模型缺少能力: reasoning, code_generation
⚠️  上下文长度不足: 需要 16384, 当前 4096
💡 建议：使用高级Agent + 大型模型
💡 替代技能：advanced_search
```

### 场景2：高级 Agent 使用基础技能

```
技能：query_article（只需要工具调用）
Agent：高级Agent（支持所有能力）
模型：大型模型（16384上下文）

结果：
✅ 完全兼容
📊 兼容度评分：100%
```

### 场景3：自动路由

```
用户请求：advanced_search（需要推理能力）
当前环境：标准Agent + 中型模型

路由决策：
1. 检查 advanced_search → 需要 REASONING，当前模型不支持
2. 查找替代技能 → [query_article]
3. 检查 query_article → 完全兼容
4. 路由到 query_article

结果：
🔄 已路由: advanced_search → query_article
原因：原技能需要推理能力，当前模型不支持；已路由到兼容度更高的技能
```

---

## 🔧 扩展指南

### 添加新技能

```python
from nlp.skill_adapter import SkillAdapter, AgentCapability, ModelCapability

adapter = SkillAdapter()

adapter.register_skill(
    name='my_custom_skill',
    func=my_function,
    description='我的自定义技能',
    category='custom',
    required_agent_capabilities={AgentCapability.MEMORY},
    required_model_capabilities={ModelCapability.REASONING},
    min_context_length=8192,
    alternatives=['fallback_skill'],
    tags=['自定义', '示例']
)
```

### 添加新 Agent 类型

```python
from nlp.agent_capability import AgentCapabilityRegistry, AgentProfile, AgentCapability

registry = AgentCapabilityRegistry()

registry.register_agent(AgentProfile(
    name='超级Agent',
    description='支持所有高级特性的超级Agent',
    capabilities={
        AgentCapability.HOOKS,
        AgentCapability.LONG_TASK,
        AgentCapability.MEMORY,
        AgentCapability.MULTI_TURN,
        AgentCapability.TOOL_USE,
        AgentCapability.CODE_EXEC,
        AgentCapability.WEB_SEARCH,
        AgentCapability.FILE_IO,
    },
    max_context_length=65536,
    supports_hooks=True,
    supports_long_tasks=True,
    supports_memory=True,
    version='5.0.0'
))
```

### 自定义路由策略

```python
from nlp.skill_router import SkillRouter

class CustomRouter(SkillRouter):
    def route_skill(self, skill_name, agent_caps, model_caps, context_length):
        # 自定义路由逻辑
        # 可以添加业务规则、优先级等
        return super().route_skill(
            skill_name, agent_caps, model_caps, context_length
        )
```

---

## 📝 技术要点

### 1. 兼容度评分算法

```
兼容度 = 已满足的要求数 / 总要求数

其中：
- 每个 Agent 能力要求占一定权重
- 每个模型能力要求占一定权重
- 上下文长度要求占一定权重
```

### 2. 替代技能排序

```
排序规则（优先级从高到低）：
1. 兼容性评分（越高越好）
2. 功能相似度（越接近越好）
3. 性能开销（越低越好）
```

### 3. 缓存策略

- 编译结果按 (技能名, Agent能力, 模型能力, 上下文长度) 缓存
- 避免重复编译相同配置
- 支持强制重新编译

---

## 🎯 总结

本演示系统完整展示了 **LLM Agent Skills 适配机制** 的三层解决方案：

1. **技能适配层**：定义能力要求，提前检查兼容性
2. **技能路由层**：智能选择最优技能，自动降级
3. **技能编译层**：编译验证配置，生成执行计划

通过这三层机制，可以有效避免用户将技能用在不适合的 Agent 和模型中，确保系统稳定运行。

---

## 📞 常见问题

**Q: 如何判断技能是否适合我的 Agent？**
A: 使用兼容性检查功能，系统会自动检查并给出评分和建议。

**Q: 如果技能不兼容怎么办？**
A: 系统会自动路由到兼容的替代技能，或者给出明确的升级建议。

**Q: 可以自定义技能吗？**
A: 可以，参考扩展指南中的示例代码。

**Q: 兼容度评分低一定不能用吗？**
A: 不一定。评分低于 100% 表示有部分能力不满足，但仍可能可用。关键看缺失的能力是否是核心要求。

---

**祝使用愉快！🎉**
