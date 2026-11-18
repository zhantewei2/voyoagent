---
name: weather-report
description: 天气播报规范：查询天气后按固定格式输出播报。
---

# 天气播报规范

用户询问天气时：

1. 调用 get_weather 工具查询目标城市。
2. 严格按以下格式输出，不要附加解释：

   今日播报｜{城市}
   天气：{weather}
