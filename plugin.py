from __future__ import annotations

from typing import Any, List, Tuple, Type

from src.plugin_system import (
    BasePlugin,
    BaseTool,
    ComponentInfo,
    ConfigField,
    ToolParamType,
    register_plugin,
)

from .client import MoegirlApiClient
from .services.query_service import MoegirlQueryService


class MoegirlLookupTool(BaseTool):
    name = "moegirl_lookup"
    description = "查询萌娘百科词条摘要与链接，用于角色、作品、设定和术语知识补充"
    parameters = [
        ("query", ToolParamType.STRING, "要查询的词条或关键词", True, None),
        ("mode", ToolParamType.STRING, "summary 或 candidates", False, ["summary", "candidates"]),
        ("max_candidates", ToolParamType.INTEGER, "候选数量上限", False, None),
    ]
    available_for_llm = True

    def _build_service(self) -> MoegirlQueryService:
        timeout_seconds = int(self.get_config("network.timeout_seconds", 10))
        prefer_exact_title = bool(self.get_config("tool.prefer_exact_title", True))
        cache_ttl_seconds = int(self.get_config("cache.ttl_seconds", 0))
        cookie_string = str(self.get_config("auth.cookie_string", "") or "").strip()
        raw_search_config = self.plugin_config.get("search", {}) if isinstance(self.plugin_config, dict) else {}
        if isinstance(raw_search_config, dict) and "prefer_generator_search" in raw_search_config:
            prefer_generator_search = bool(raw_search_config.get("prefer_generator_search", True))
        elif isinstance(raw_search_config, dict) and "prefer_authenticated_search" in raw_search_config:
            prefer_generator_search = bool(raw_search_config.get("prefer_authenticated_search", True))
        else:
            prefer_generator_search = bool(self.get_config("search.prefer_generator_search", True))
        client = MoegirlApiClient(timeout_seconds=timeout_seconds, cookie_string=cookie_string)
        return MoegirlQueryService(
            client=client,
            prefer_exact_title=prefer_exact_title,
            cache_ttl_seconds=cache_ttl_seconds,
            enable_generator_search=prefer_generator_search,
        )

    def _format_result(self, result: Any) -> str:
        if result.status == "ok" and result.page is not None:
            lines = [
                f"词条：{result.page.title}",
                f"简介：{result.page.summary}",
                f"链接：{result.page.url}",
            ]
            if result.page.categories:
                lines.append("分类：" + "、".join(result.page.categories[:3]))
            if result.page.thumbnail_url:
                lines.append(f"缩略图：{result.page.thumbnail_url}")
            if result.candidates:
                lines.append("")
                lines.append("相关语境：")
                for index, item in enumerate(result.candidates, start=1):
                    lines.append(f"{index}. {item.title}")
                    if item.description:
                        lines.append(f"简介：{item.description}")
                    lines.append(f"链接：{item.url}")
            return "\n".join(lines)

        if result.status == "ambiguous":
            lines = [result.message or "以下词条可能相关："]
            for index, item in enumerate(result.candidates, start=1):
                lines.append(f"{index}. {item.title}")
                if item.description:
                    lines.append(f"简介：{item.description}")
                lines.append(f"链接：{item.url}")
            return "\n".join(lines)

        if result.status == "not_found":
            return result.message or "未找到明显匹配词条。"

        return result.message or "萌娘百科查询暂时不可用。"

    async def execute(self, function_args: dict[str, Any]) -> dict[str, Any]:
        query = str(function_args.get("query", "")).strip()
        if not query:
            return {"name": self.name, "content": "查询词不能为空。"}

        mode = str(function_args.get("mode", "summary") or "summary")
        max_candidates = int(function_args.get("max_candidates", self.get_config("result.max_candidates", 5)))
        service = self._build_service()
        result = await service.lookup(query, mode=mode, max_candidates=max_candidates)
        return {"name": self.name, "content": self._format_result(result)}


@register_plugin
class MoegirlWikiPlugin(BasePlugin):
    plugin_name = "moegirl_wiki_plugin"
    enable_plugin = True
    dependencies = []
    python_dependencies = []
    config_file_name = "config.toml"
    config_schema = {
        "plugin": {
            "enabled": ConfigField(type=bool, default=True, description="是否启用插件"),
            "config_version": ConfigField(type=str, default="1.0.0", description="配置文件版本"),
        },
        "network": {
            "timeout_seconds": ConfigField(type=int, default=10, description="请求超时时间（秒）"),
        },
        "auth": {
            "mode": ConfigField(
                type=str,
                default="anonymous",
                description="认证模式",
                choices=["anonymous", "cookie"],
            ),
            "cookie_string": ConfigField(
                type=str,
                default="",
                description="萌娘百科登录 Cookie",
                input_type="textarea",
                rows=4,
                placeholder="例如：session=...; token=...",
                hint="可选。当前搜索主路径不依赖 Cookie，但保留登录态配置用于后续扩展；建议仅保存在本地配置中。",
            ),
        },
        "search": {
            "prefer_generator_search": ConfigField(
                type=bool,
                default=True,
                description="优先使用 generator=search 搜索接口",
            ),
        },
        "cache": {
            "ttl_seconds": ConfigField(type=int, default=300, description="缓存生存时间（秒）"),
        },
        "result": {
            "max_candidates": ConfigField(type=int, default=5, description="候选词条数量上限"),
        },
        "tool": {
            "prefer_exact_title": ConfigField(type=bool, default=True, description="是否优先精确标题匹配"),
        },
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        return [(MoegirlLookupTool.get_tool_info(), MoegirlLookupTool)]
