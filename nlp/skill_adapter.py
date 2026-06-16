"""
技能适配层（Skill Adapter Layer）
定义技能元数据、能力要求，以及技能与Agent/模型的适配关系
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable, Any
from enum import Enum


class AgentCapability(Enum):
    """Agent能力类型枚举"""
    HOOKS = "hooks"                    # 支持钩子机制
    LONG_TASK = "long_task"           # 支持长时任务
    MEMORY = "memory"                 # 支持记忆
    MULTI_TURN = "multi_turn"         # 支持多轮对话
    TOOL_USE = "tool_use"             # 支持工具调用
    CODE_EXEC = "code_exec"           # 支持代码执行
    WEB_SEARCH = "web_search"         # 支持网络搜索
    FILE_IO = "file_io"               # 支持文件读写


class ModelCapability(Enum):
    """大模型能力类型枚举"""
    CONTEXT_LENGTH = "context_length"       # 上下文长度
    REASONING = "reasoning"                 # 推理能力
    CODE_GENERATION = "code_generation"     # 代码生成
    MULTI_LANGUAGE = "multi_language"       # 多语言支持
    VISION = "vision"                       # 视觉理解
    FUNCTION_CALLING = "function_calling"   # 函数调用


@dataclass
class SkillRequirement:
    """技能能力要求"""
    required_agent_capabilities: Set[AgentCapability] = field(default_factory=set)
    required_model_capabilities: Set[ModelCapability] = field(default_factory=set)
    min_context_length: int = 0          # 最小上下文长度要求
    max_execution_time: int = 30         # 最大执行时间（秒）
    requires_memory: bool = False        # 是否需要记忆


@dataclass
class SkillMetadata:
    """技能元数据"""
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    category: str = "general"            # 技能分类
    requirements: SkillRequirement = field(default_factory=SkillRequirement)
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他技能
    alternatives: List[str] = field(default_factory=list)  # 可替代的技能
    tags: List[str] = field(default_factory=list)          # 标签


class SkillAdapter:
    """
    技能适配器
    负责管理技能的元数据、能力要求，并提供适配性检查
    """
    
    def __init__(self):
        self.skills: Dict[str, Dict] = {}
    
    def register_skill(
        self,
        name: str,
        func: Callable,
        description: str,
        version: str = "1.0.0",
        category: str = "general",
        required_agent_capabilities: Set[AgentCapability] = None,
        required_model_capabilities: Set[ModelCapability] = None,
        min_context_length: int = 0,
        max_execution_time: int = 30,
        dependencies: List[str] = None,
        alternatives: List[str] = None,
        tags: List[str] = None,
        **kwargs
    ):
        """
        注册技能并定义其能力要求
        
        Args:
            name: 技能名称
            func: 技能执行函数
            description: 技能描述
            version: 版本号
            category: 技能分类
            required_agent_capabilities: 需要的Agent能力
            required_model_capabilities: 需要的大模型能力
            min_context_length: 最小上下文长度
            max_execution_time: 最大执行时间
            dependencies: 依赖的技能列表
            alternatives: 可替代的技能列表
            tags: 标签列表
        """
        self.skills[name] = {
            'func': func,
            'metadata': SkillMetadata(
                name=name,
                description=description,
                version=version,
                category=category,
                requirements=SkillRequirement(
                    required_agent_capabilities=required_agent_capabilities or set(),
                    required_model_capabilities=required_model_capabilities or set(),
                    min_context_length=min_context_length,
                    max_execution_time=max_execution_time,
                ),
                dependencies=dependencies or [],
                alternatives=alternatives or [],
                tags=tags or [],
            ),
            'kwargs': kwargs
        }
    
    def check_skill_compatibility(
        self,
        skill_name: str,
        agent_capabilities: Set[AgentCapability],
        model_capabilities: Set[ModelCapability],
        context_length: int = 4096
    ) -> Dict[str, Any]:
        """
        检查技能与Agent和模型的兼容性
        
        Returns:
            {
                'compatible': bool,          # 是否兼容
                'score': float,              # 兼容度评分 (0-1)
                'missing_agent_caps': set,   # 缺失的Agent能力
                'missing_model_caps': set,   # 缺失的模型能力
                'warnings': List[str],       # 警告信息
                'recommendations': List[str] # 建议
            }
        """
        if skill_name not in self.skills:
            return {
                'compatible': False,
                'score': 0.0,
                'missing_agent_caps': set(),
                'missing_model_caps': set(),
                'warnings': [f"技能 '{skill_name}' 不存在"],
                'recommendations': []
            }
        
        skill = self.skills[skill_name]
        requirements = skill['metadata'].requirements
        
        # 检查Agent能力
        missing_agent_caps = requirements.required_agent_capabilities - agent_capabilities
        
        # 检查模型能力
        missing_model_caps = requirements.required_model_capabilities - model_capabilities
        
        # 检查上下文长度
        context_ok = context_length >= requirements.min_context_length
        
        # 计算兼容度评分
        total_requirements = (
            len(requirements.required_agent_capabilities) + 
            len(requirements.required_model_capabilities) +
            (1 if requirements.min_context_length > 0 else 0)
        )
        
        met_requirements = (
            (len(requirements.required_agent_capabilities) - len(missing_agent_caps)) +
            (len(requirements.required_model_capabilities) - len(missing_model_caps)) +
            (1 if context_ok else 0)
        )
        
        score = met_requirements / total_requirements if total_requirements > 0 else 1.0
        
        # 生成警告和建议
        warnings = []
        recommendations = []
        
        if missing_agent_caps:
            warnings.append(f"Agent缺少能力: {', '.join([c.value for c in missing_agent_caps])}")
            recommendations.append(f"考虑使用支持 {', '.join([c.value for c in missing_agent_caps])} 的Agent")
        
        if missing_model_caps:
            warnings.append(f"模型缺少能力: {', '.join([c.value for c in missing_model_caps])}")
            recommendations.append(f"考虑使用支持 {', '.join([c.value for c in missing_model_caps])} 的模型")
        
        if not context_ok:
            warnings.append(f"上下文长度不足: 需要 {requirements.min_context_length}, 当前 {context_length}")
            recommendations.append("使用更长上下文的模型或缩短输入")
        
        # 检查替代技能
        if not (missing_agent_caps or missing_model_caps) and score < 1.0:
            alternatives = skill['metadata'].alternatives
            if alternatives:
                recommendations.append(f"可考虑替代技能: {', '.join(alternatives)}")
        
        return {
            'compatible': len(missing_agent_caps) == 0 and len(missing_model_caps) == 0 and context_ok,
            'score': score,
            'missing_agent_caps': missing_agent_caps,
            'missing_model_caps': missing_model_caps,
            'warnings': warnings,
            'recommendations': recommendations
        }
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict]:
        """获取技能信息"""
        if skill_name not in self.skills:
            return None
        skill = self.skills[skill_name]
        return {
            'name': skill['metadata'].name,
            'description': skill['metadata'].description,
            'version': skill['metadata'].version,
            'category': skill['metadata'].category,
            'requirements': {
                'agent_capabilities': [c.value for c in skill['metadata'].requirements.required_agent_capabilities],
                'model_capabilities': [c.value for c in skill['metadata'].requirements.required_model_capabilities],
                'min_context_length': skill['metadata'].requirements.min_context_length,
                'max_execution_time': skill['metadata'].requirements.max_execution_time,
            },
            'dependencies': skill['metadata'].dependencies,
            'alternatives': skill['metadata'].alternatives,
            'tags': skill['metadata'].tags,
        }
    
    def list_skills(self, category: str = None) -> List[Dict]:
        """列出所有技能（可按分类过滤）"""
        skills_list = []
        for name, skill in self.skills.items():
            if category and skill['metadata'].category != category:
                continue
            skills_list.append(self.get_skill_info(name))
        return skills_list
