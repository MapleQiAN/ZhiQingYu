"""
干预模块管理器
"""
import json
from pathlib import Path
from typing import Optional
from app.schemas.style import InterventionConfig


class InterventionManager:
    """干预模块管理器"""
    
    def __init__(self):
        self._interventions: dict[str, InterventionConfig] = {}
        self._load_interventions()
    
    def _load_interventions(self):
        """加载干预模块配置"""
        config_path = Path(__file__).parent.parent / "config" / "interventions.json"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for interv_data in data.get("interventions", []):
                    interv = InterventionConfig(**interv_data)
                    self._interventions[interv.id] = interv
        except Exception as e:
            print(f"加载干预模块配置失败: {e}")
    
    def get_intervention(self, interv_id: str) -> Optional[InterventionConfig]:
        """获取指定干预模块"""
        return self._interventions.get(interv_id)
    
    def get_all_interventions(self) -> list[InterventionConfig]:
        """获取所有干预模块"""
        return list(self._interventions.values())


# 全局单例
_intervention_manager: Optional[InterventionManager] = None


def get_intervention_manager() -> InterventionManager:
    """获取干预模块管理器单例"""
    global _intervention_manager
    if _intervention_manager is None:
        _intervention_manager = InterventionManager()
    return _intervention_manager


