"""
Agent能力描述模块
定义不同类型Agent和大模型的能力特征
"""
from dataclasses import dataclass, field
from typing import Set, Dict, List, Optional
from nlp.skill_adapter import AgentCapability, ModelCapability


@dataclass
class AgentProfile:
    """Agent能力画像"""
    name: str
    description: str
    capabilities: Set[AgentCapability]
    max_context_length: int = 4096
    supports_hooks: bool = False
    supports_long_tasks: bool = False
    supports_memory: bool = False
    version: str = "1.0.0"
    metadata: Dict = field(default_factory=dict)


@dataclass
class ModelProfile:
    """大模型能力画像"""
    name: str
    description: str
    capabilities: Set[ModelCapability]
    context_length: int = 4096
    version: str = "1.0.0"
    provider: str = ""
    metadata: Dict = field(default_factory=dict)


class AgentCapabilityRegistry:
    """
    Agent能力注册表
    管理预定义的Agent和模型能力配置
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentProfile] = {}
        self.models: Dict[str, ModelProfile] = {}
        self._init_default_agents()
        self._init_default_models()
    
    def _init_default_agents(self):
        """初始化预定义的Agent类型"""
        
        # 基础Agent - 只支持基本功能
        self.agents['basic'] = AgentProfile(
            name='基础Agent',
            description='最简单的Agent实现，仅支持基本意图识别和技能调用',
            capabilities={
                AgentCapability.TOOL_USE,
            },
            max_context_length=4096,
            supports_hooks=False,
            supports_long_tasks=False,
            supports_memory=False,
            version='1.0.0'
        )
        
        # 标准Agent - 支持多轮对话
        self.agents['standard'] = AgentProfile(
            name='标准Agent',
            description='支持多轮对话和简单记忆的Agent',
            capabilities={
                AgentCapability.TOOL_USE,
                AgentCapability.MULTI_TURN,
                AgentCapability.MEMORY,
            },
            max_context_length=8192,
            supports_hooks=False,
            supports_long_tasks=False,
            supports_memory=True,
            version='2.0.0'
        )
        
        # 高级Agent - 支持钩子和长时任务
        self.agents['advanced'] = AgentProfile(
            name='高级Agent',
            description='支持钩子机制、长时任务和完整记忆功能',
            capabilities={
                AgentCapability.HOOKS,
                AgentCapability.LONG_TASK,
                AgentCapability.MEMORY,
                AgentCapability.MULTI_TURN,
                AgentCapability.TOOL_USE,
                AgentCapability.CODE_EXEC,
            },
            max_context_length=16384,
            supports_hooks=True,
            supports_long_tasks=True,
            supports_memory=True,
            version='3.0.0'
        )
        
        # 企业级Agent - 完整能力
        self.agents['enterprise'] = AgentProfile(
            name='企业级Agent',
            description='完整的企业级Agent，支持所有高级特性',
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
            max_context_length=32768,
            supports_hooks=True,
            supports_long_tasks=True,
            supports_memory=True,
            version='4.0.0'
        )
    
    def _init_default_models(self):
        """初始化预定义的模型类型"""
        
        # 小型模型
        self.models['small'] = ModelProfile(
            name='小型模型',
            description='参数量较小的模型，适合简单任务',
            capabilities={
                ModelCapability.CONTEXT_LENGTH,
            },
            context_length=4096,
            version='1.0.0',
            provider='generic'
        )
        
        # 中型模型
        self.models['medium'] = ModelProfile(
            name='中型模型',
            description='平衡性能和成本的模型',
            capabilities={
                ModelCapability.CONTEXT_LENGTH,
                ModelCapability.REASONING,
                ModelCapability.MULTI_LANGUAGE,
                ModelCapability.FUNCTION_CALLING,
            },
            context_length=8192,
            version='2.0.0',
            provider='generic'
        )
        
        # 大型模型
        self.models['large'] = ModelProfile(
            name='大型模型',
            description='强大的推理和代码生成能力',
            capabilities={
                ModelCapability.CONTEXT_LENGTH,
                ModelCapability.REASONING,
                ModelCapability.CODE_GENERATION,
                ModelCapability.MULTI_LANGUAGE,
                ModelCapability.FUNCTION_CALLING,
            },
            context_length=16384,
            version='3.0.0',
            provider='generic'
        )
        
        # 超大型模型
        self.models['xl'] = ModelProfile(
            name='超大型模型',
            description='最强大的模型，支持所有高级能力',
            capabilities={
                ModelCapability.CONTEXT_LENGTH,
                ModelCapability.REASONING,
                ModelCapability.CODE_GENERATION,
                ModelCapability.MULTI_LANGUAGE,
                ModelCapability.VISION,
                ModelCapability.FUNCTION_CALLING,
            },
            context_length=32768,
            version='4.0.0',
            provider='generic'
        )
    
    def register_agent(self, profile: AgentProfile):
        """注册自定义Agent"""
        self.agents[profile.name.lower()] = profile
    
    def register_model(self, profile: ModelProfile):
        """注册自定义模型"""
        self.models[profile.name.lower()] = profile
    
    def get_agent(self, name: str) -> Optional[AgentProfile]:
        """获取Agent配置"""
        return self.agents.get(name.lower())
    
    def get_model(self, name: str) -> Optional[ModelProfile]:
        """获取模型配置"""
        return self.models.get(name.lower())
    
    def list_agents(self) -> List[Dict]:
        """列出所有Agent"""
        return [
            {
                'key': key,
                'name': profile.name,
                'description': profile.description,
                'capabilities': [c.value for c in profile.capabilities],
                'max_context_length': profile.max_context_length,
                'supports_hooks': profile.supports_hooks,
                'supports_long_tasks': profile.supports_long_tasks,
                'supports_memory': profile.supports_memory,
            }
            for key, profile in self.agents.items()
        ]
    
    def list_models(self) -> List[Dict]:
        """列出所有模型"""
        return [
            {
                'key': key,
                'name': profile.name,
                'description': profile.description,
                'capabilities': [c.value for c in profile.capabilities],
                'context_length': profile.context_length,
                'provider': profile.provider,
            }
            for key, profile in self.models.items()
        ]
    
    def get_agent_comparison(self, agent_keys: List[str]) -> Dict:
        """比较多个Agent的能力"""
        comparison = {}
        for key in agent_keys:
            agent = self.get_agent(key)
            if agent:
                comparison[key] = {
                    'name': agent.name,
                    'capabilities': sorted([c.value for c in agent.capabilities]),
                    'max_context_length': agent.max_context_length,
                    'supports_hooks': agent.supports_hooks,
                    'supports_long_tasks': agent.supports_long_tasks,
                    'supports_memory': agent.supports_memory,
                }
        return comparison
    
    def get_model_comparison(self, model_keys: List[str]) -> Dict:
        """比较多个模型的能力"""
        comparison = {}
        for key in model_keys:
            model = self.get_model(key)
            if model:
                comparison[key] = {
                    'name': model.name,
                    'capabilities': sorted([c.value for c in model.capabilities]),
                    'context_length': model.context_length,
                    'provider': model.provider,
                }
        return comparison
