"""
技能编译器（Skill Compiler）
编译和验证技能适配性，生成可执行的技能配置
"""
from typing import Dict, List, Optional, Any, Set, Tuple
from nlp.skill_adapter import SkillAdapter, AgentCapability, ModelCapability
from nlp.skill_router import SkillRouter
import json


class SkillCompiler:
    """
    技能编译器
    负责编译技能配置、验证依赖关系、生成优化后的技能执行计划
    """
    
    def __init__(self, skill_adapter: SkillAdapter, skill_router: SkillRouter):
        """
        Args:
            skill_adapter: 技能适配器
            skill_router: 技能路由器
        """
        self.skill_adapter = skill_adapter
        self.skill_router = skill_router
        self.compiled_cache: Dict[str, Dict] = {}
    
    def compile_skill(
        self,
        skill_name: str,
        agent_capabilities: Set[AgentCapability],
        model_capabilities: Set[ModelCapability],
        context_length: int = 4096,
        force_recompile: bool = False
    ) -> Dict[str, Any]:
        """
        编译技能配置
        
        编译流程：
        1. 检查缓存
        2. 验证技能存在性
        3. 检查能力兼容性
        4. 解析依赖关系
        5. 路由到最优技能
        6. 生成执行计划
        
        Args:
            skill_name: 技能名称
            agent_capabilities: Agent能力
            model_capabilities: 模型能力
            context_length: 上下文长度
            force_recompile: 强制重新编译
            
        Returns:
            {
                'success': bool,                    # 编译成功
                'skill_name': str,                  # 技能名称
                'compiled_skill': str,              # 编译后的技能名称
                'execution_plan': List[str],        # 执行计划
                'compatibility': Dict,              # 兼容性信息
                'dependencies_resolved': bool,      # 依赖是否解析
                'warnings': List[str],              # 警告
                'optimized': bool,                  # 是否经过优化
            }
        """
        # 1. 检查缓存
        cache_key = f"{skill_name}_{frozenset(agent_capabilities)}_{frozenset(model_capabilities)}_{context_length}"
        if not force_recompile and cache_key in self.compiled_cache:
            return self.compiled_cache[cache_key]
        
        result = {
            'success': False,
            'skill_name': skill_name,
            'compiled_skill': skill_name,
            'execution_plan': [],
            'compatibility': {},
            'dependencies_resolved': False,
            'warnings': [],
            'optimized': False,
            'cache_key': cache_key
        }
        
        # 2. 验证技能存在性
        if skill_name not in self.skill_adapter.skills:
            result['warnings'].append(f"技能 '{skill_name}' 不存在")
            self.compiled_cache[cache_key] = result
            return result
        
        # 3. 检查能力兼容性
        compatibility = self.skill_adapter.check_skill_compatibility(
            skill_name,
            agent_capabilities,
            model_capabilities,
            context_length
        )
        result['compatibility'] = compatibility
        
        # 4. 解析依赖关系
        deps_resolved, dep_warnings = self._resolve_dependencies(
            skill_name,
            agent_capabilities,
            model_capabilities,
            context_length
        )
        result['dependencies_resolved'] = deps_resolved
        result['warnings'].extend(dep_warnings)
        
        # 5. 路由到最优技能
        routing_info = self.skill_router.route_skill(
            skill_name,
            agent_capabilities,
            model_capabilities,
            context_length
        )
        
        result['compiled_skill'] = routing_info['routed_skill']
        result['optimized'] = routing_info['was_rerouted']
        
        if routing_info['was_rerouted']:
            result['warnings'].append(f"已路由: {skill_name} → {routing_info['routed_skill']}")
            result['warnings'].append(f"路由原因: {routing_info['reason']}")
        
        # 6. 生成执行计划
        execution_plan = self._generate_execution_plan(
            routing_info['routed_skill'],
            skill_name,
            deps_resolved
        )
        result['execution_plan'] = execution_plan
        
        # 7. 设置成功标志
        result['success'] = compatibility['compatible'] or deps_resolved
        
        # 8. 缓存结果
        self.compiled_cache[cache_key] = result
        
        return result
    
    def _resolve_dependencies(
        self,
        skill_name: str,
        agent_capabilities: Set[AgentCapability],
        model_capabilities: Set[ModelCapability],
        context_length: int
    ) -> Tuple[bool, List[str]]:
        """
        解析技能依赖关系
        
        Returns:
            (是否全部解析, 警告列表)
        """
        if skill_name not in self.skill_adapter.skills:
            return False, [f"技能 '{skill_name}' 不存在"]
        
        skill = self.skill_adapter.skills[skill_name]
        dependencies = skill['metadata'].dependencies
        
        if not dependencies:
            return True, []
        
        warnings = []
        all_resolved = True
        
        for dep_name in dependencies:
            if dep_name not in self.skill_adapter.skills:
                warnings.append(f"依赖技能 '{dep_name}' 不存在")
                all_resolved = False
                continue
            
            # 检查依赖技能的兼容性
            dep_compat = self.skill_adapter.check_skill_compatibility(
                dep_name,
                agent_capabilities,
                model_capabilities,
                context_length
            )
            
            if not dep_compat['compatible']:
                warnings.append(f"依赖技能 '{dep_name}' 不完全兼容: {', '.join(dep_compat['warnings'])}")
                # 依赖不兼容但不阻塞，只是警告
        
        return all_resolved, warnings
    
    def _generate_execution_plan(
        self,
        compiled_skill: str,
        original_skill: str,
        deps_resolved: bool
    ) -> List[str]:
        """
        生成执行计划
        
        Returns:
            执行步骤列表
        """
        plan = []
        
        # 步骤1: 初始化
        plan.append("1. 初始化技能执行环境")
        
        # 步骤2: 加载依赖
        if compiled_skill in self.skill_adapter.skills:
            skill = self.skill_adapter.skills[compiled_skill]
            if skill['metadata'].dependencies:
                plan.append(f"2. 加载依赖技能: {', '.join(skill['metadata'].dependencies)}")
        
        # 步骤3: 技能路由（如果需要）
        if compiled_skill != original_skill:
            plan.append(f"3. 技能路由: {original_skill} → {compiled_skill}")
        else:
            plan.append(f"3. 使用原技能: {compiled_skill}")
        
        # 步骤4: 执行技能
        plan.append(f"4. 执行技能: {compiled_skill}")
        
        # 步骤5: 结果处理
        plan.append("5. 处理和格式化结果")
        
        # 步骤6: 清理
        plan.append("6. 清理执行环境")
        
        return plan
    
    def batch_compile(
        self,
        skill_names: List[str],
        agent_capabilities: Set[AgentCapability],
        model_capabilities: Set[ModelCapability],
        context_length: int = 4096
    ) -> Dict[str, Dict]:
        """
        批量编译技能
        
        Returns:
            {skill_name: compile_result}
        """
        results = {}
        for skill_name in skill_names:
            results[skill_name] = self.compile_skill(
                skill_name,
                agent_capabilities,
                model_capabilities,
                context_length
            )
        return results
    
    def get_compilation_report(
        self,
        compile_result: Dict
    ) -> str:
        """
        生成编译报告（文本格式）
        
        Returns:
            格式化的编译报告
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"技能编译报告: {compile_result['skill_name']}")
        lines.append("=" * 60)
        
        lines.append(f"\n✓ 编译状态: {'成功' if compile_result['success'] else '失败'}")
        lines.append(f"✓ 编译后技能: {compile_result['compiled_skill']}")
        lines.append(f"✓ 依赖解析: {'完成' if compile_result['dependencies_resolved'] else '未完成'}")
        lines.append(f"✓ 是否优化: {'是' if compile_result['optimized'] else '否'}")
        
        # 兼容性信息
        if compile_result['compatibility']:
            compat = compile_result['compatibility']
            lines.append(f"\n📊 兼容性评分: {compat['score']:.0%}")
            if compat['warnings']:
                lines.append("⚠️  警告:")
                for warning in compat['warnings']:
                    lines.append(f"   - {warning}")
            if compat['recommendations']:
                lines.append("💡 建议:")
                for rec in compat['recommendations']:
                    lines.append(f"   - {rec}")
        
        # 编译警告
        if compile_result['warnings']:
            lines.append(f"\n⚠️  编译警告:")
            for warning in compile_result['warnings']:
                lines.append(f"   - {warning}")
        
        # 执行计划
        if compile_result['execution_plan']:
            lines.append(f"\n📋 执行计划:")
            for step in compile_result['execution_plan']:
                lines.append(f"   {step}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def clear_cache(self):
        """清空编译缓存"""
        self.compiled_cache.clear()
