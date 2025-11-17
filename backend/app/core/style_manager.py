"""
风格系统管理器
"""
import json
import os
from pathlib import Path
from typing import Optional
from app.schemas.style import StyleProfile


class StyleManager:
    """风格系统管理器"""
    
    def __init__(self):
        self._styles: dict[str, StyleProfile] = {}
        self._load_styles()
    
    def _load_styles(self):
        """加载风格配置"""
        config_path = Path(__file__).parent.parent / "config" / "styles.json"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for style_data in data.get("styles", []):
                    style = StyleProfile(**style_data)
                    self._styles[style.id] = style
        except Exception as e:
            print(f"加载风格配置失败: {e}")
            # 如果加载失败，使用默认的危机安全风格
            self._styles["crisis_safe"] = StyleProfile(
                id="crisis_safe",
                name="危机安全响应",
                description="默认安全风格",
                tone="gentle",
                directness=2,
                analysisDepth=2,
                emotionFocus=5,
                actionFocus=2,
                jokingLevel=0,
                confrontationLevel=0,
                useGentleQuestions=True,
                usePsychoEducation=False,
                safetyBias="high"
            )
    
    def get_style(self, style_id: str) -> Optional[StyleProfile]:
        """获取指定风格"""
        return self._styles.get(style_id)
    
    def get_all_styles(self) -> list[StyleProfile]:
        """获取所有风格（排除系统内部风格）"""
        return [
            style for style in self._styles.values()
            if style.id != "crisis_safe"
        ]
    
    def get_default_style(self) -> StyleProfile:
        """获取默认风格（mentor）"""
        return self._styles.get("mentor") or list(self._styles.values())[0]


# 全局单例
_style_manager: Optional[StyleManager] = None


def get_style_manager() -> StyleManager:
    """获取风格管理器单例"""
    global _style_manager
    if _style_manager is None:
        _style_manager = StyleManager()
    return _style_manager


