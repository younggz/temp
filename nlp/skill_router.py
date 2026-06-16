"""
技能路由层（Skill Router）
实现替代技能路由机制，当主技能不兼容时自动路由到替代技能
"""
from typing import Dict, List, Optional, Any, Set
from nlp.skill_adapter import SkillAdapter, AgentCapability, ModelCapability


class SkillRouter:
    """
    技能路由器
    负责在技能不兼容时，智能路由到最合适的替代技能
    """
    
    def __init__(self, skill_adapter: SkillAdapter):
        """
        Args:
            skill_adapter: 技能适配器实例
        """
        self.skill_adapter = skill_adapter
        self.routing_history: List[Dict] = []
    
    def route_skill(
        self,
        skill_name: str,
        agent_capabilities: Set[AgentCapability],
        model_capabilities: Set[ModelCapability],
        context_length: int = 4096,
        prefer_alternatives: bool = True
    ) -> Dict[str, Any]:
        """
        路由技能调用
        
        流程：
        1. 检查主技能兼容性
        2. 如果兼容，直接执行
        3. 如果不兼容，查找替代技能
        4. 对替代技能进行兼容性排序
        5. 返回最优技能及路由信息
        
        Args:
            skill_name: 请求的技能名称
            agent_capabilities: Agent能力集合
            model_capabilities: 模型能力集合
            context_length: 上下文长度
            prefer_alternatives: 是否优先使用替代技能
            
        Returns:
            {
                'original_skill': str,          # 原始请求技能
                'routed_skill': str,            # 实际路由技能
                'was_rerouted': bool,           # 是否被重路由
                'compatibility': Dict,          # 兼容性检查结果
                'alternatives': List[Dict],     # 替代技能列表
                'reason': str,                  # 路由原因
            }
        """
        # 1. 检查主技能兼容性
        original_check = self.skill_adapter.check_skill_compatibility(
            skill_name,
            agent_capabilities,
            model_capabilities,
            context_length
        )
        
        # 2. 如果主技能兼容且不需要替代，直接返回
        if original_check['compatible'] and not prefer_alternatives:
            return {
                'original_skill': skill_name,
                'routed_skill': skill_name,
                'was_rerouted': False,
                'compatibility': original_check,
                'alternatives': [],
                'reason': '主技能完全兼容'
            }
        
        # 3. 查找替代技能
        alternatives = self._find_and_rank_alternatives(
            skill_name,
            agent_capabilities,
            model_capabilities,
            context_length
        )
        
        # 4. 决定路由目标
        if alternatives:
            best_alternative = alternatives[0]
            was_rerouted = (best_alternative['name'] != skill_name)
            
            routing_info = {
                'original_skill': skill_name,
                'routed_skill': best_alternative['name'],
                'was_rerouted': was_rerouted,
                'compatibility': best_alternative['compatibility'],
                'alternatives': alternatives,
                'reason': self._generate_routing_reason(
                    skill_name,
                    best_alternative['name'],
                    original_check,
                    best_alternative['compatibility']
                )
            }
        else:
            routing_info = {
                'original_skill': skill_name,
                'routed_skill': skill_name,
                'was_rerouted': False,
                'compatibility': original_check,
                'alternatives': [],
                'reason': '无可用替代技能，尝试使用原技能'
            }
        
        # 5. 记录路由历史
        self.routing_history.append({
            'timestamp': len(self.routing_history),
            **routing_info
        })
        
        return routing_info
    
    def _find_and_rank_alternatives(
        self,
        skill_name: str,
        agent_capabilities: Set[AgentCapability],
        model_capabilities: Set[ModelCapability],
        context_length: int
    ) -> List[Dict]:
        """
        查找并排序替代技能
        
        Returns:
            按兼容度排序的替代技能列表
        """
        if skill_name not in self.skill_adapter.skills:
            return []
        
        skill = self.skill_adapter.skills[skill_name]
        alternative_names = skill['metadata'].alternatives
        
        if not alternative_names:
            return []
        
        alternatives = []
        for alt_name in alternative_names:
            if alt_name not in self.skill_adapter.skills:
                continue
            
            compat = self.skill_adapter.check_skill_compatibility(
                alt_name,
                agent_capabilities,
                model_capabilities,
                context_length
            )
            
            alternatives.append({
                'name': alt_name,
                'compatibility': compat,
                'metadata': self.skill_adapter.get_skill_info(alt_name)
            })
        
        # 按兼容度评分降序排序
        alternatives.sort(key=lambda x: x['compatibility']['score'], reverse=True)
        
        return alternatives
    
    def _generate_routing_reason(
        self,
        original: str,
        routed: str,
        original_check: Dict,
        routed_check: Dict
    ) -> str:
        """生成路由原因说明"""
        if original == routed:
            return f"技能 '{original}' 完全兼容，无需路由"
        
        reasons = []
        
        if original_check['missing_agent_caps']:
            reasons.append(f"原技能需要Agent能力: {', '.join([c.value for c in original_check['missing_agent_caps']])}")
        
        if original_check['missing_model_caps']:
            reasons.append(f"原技能需要模型能力: {', '.join([c.value for c in original_check['missing_model_caps']])}")
        
        if original_check['score'] < 1.0 and not (original_check['missing_agent_caps'] or original_check['missing_model_caps']):
            reasons.append(f"原技能兼容度较低 ({original_check['score']:.0%})")
        
        reasons.append(f"已路由到兼容度更高的技能 '{routed}' ({routed_check['score']:.0%})")
        
        return "；".join(reasons)
    
    def get_routing_history(self, limit: int = 10) -> List[Dict]:
        """获取路由历史"""
        return self.routing_history[-limit:]
    
    def clear_routing_history(self):
        """清空路由历史"""
        self.routing_history.clear()
