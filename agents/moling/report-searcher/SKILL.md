---
name: report-searcher
description: 搜索权威行业报告、白皮书、PDF 文件的专用 skill。使用 SearXNG 搜索引擎配合高级搜索运算符精准定位 Deloitte、麦肯锡、艾瑞咨询、政府统计等权威机构的报告。当用户要求搜索某个主题的报告、白皮书、行业分析时使用此 skill。
---

# Report Searcher

## 核心搜索策略

使用 SearXNG 搜索引擎（`web_search` 工具）配合高级搜索运算符，精准定位权威行业报告、白皮书、PDF 文件。

## 搜索运算符优先级

按效果从高到低使用以下运算符组合：

### 1. filetype:pdf（最重要）
只显示 PDF 文件，完美匹配报告格式。

**示例：**
- `新能源汽车 filetype:pdf`
- `"行业报告" 人工智能 filetype:pdf 2025`
- `"market report" "electric vehicle" filetype:pdf`

### 2. inurl:report OR inurl:whitepaper OR inurl:白皮书
URL 中包含这些词的页面，通常是正式报告。

**示例：**
- `人工智能 inurl:report filetype:pdf`

### 3. site: 限制特定权威网站
只在知名机构官网搜索，避免垃圾结果。

**权威站点列表：**
- `site:deloitte.com` - 德勤
- `site:pwc.com` - 普华永道
- `site:ey.com` - 安永
- `site:kpmg.com` - 毕马威
- `site:mckinsey.com` - 麦肯锡
- `site:iresearch.com.cn` - 艾瑞咨询
- `site:stats.gov.cn` - 中国国家统计局
- `site:singstat.gov.sg` - 新加坡统计局

**示例：**
- `site:deloitte.com 人工智能 report filetype:pdf`
- `site:pwc.com OR site:ey.com OR site:kpmg.com "中国" 行业报告 filetype:pdf`
- `site:mckinsey.com "industry analysis" filetype:pdf`
- `site:iresearch.com.cn 报告 filetype:pdf`

### 4. 引号 " "（精确匹配短语）
强制搜索完整词组，避免拆散。

**示例：**
- `"中国新能源汽车市场报告" filetype:pdf`

### 5. 时间限制（最近报告）
优先搜索 2025-2026 年的报告。

**示例：**
- `新能源汽车报告 filetype:pdf after:2025`
- `人工智能 filetype:pdf 2025 OR 2026`

### 6. 排除无关结果（减号 -）
去掉销售页面、下载页面等垃圾结果。

**示例：**
- `新能源汽车报告 filetype:pdf -购买 -下载页面`

## 组合查询模板（直接使用）

### 通用行业报告
```
[行业] 行业报告 OR 白皮书 OR market report filetype:pdf 2025 OR 2026
```

### 咨询公司报告
```
(deloitte OR pwc OR ey OR kpmg OR mckinsey) [行业] (report OR whitepaper) filetype:pdf
```

### 中国/中文报告
```
"[行业] 行业研究报告" OR "[行业] 白皮书" filetype:pdf site:.cn
```

### 政府/官方统计
```
[行业] statistics OR 数据 filetype:pdf site:gov OR site:gov.sg
```

### 学术/研究型
```
[行业] industry analysis OR research report filetype:pdf
```

## 工作流程

当用户要求搜索某个主题的报告时：

1. **构建搜索查询**
   - 使用上述运算符组合，优先使用 `filetype:pdf`
   - 根据主题选择合适的权威站点（site:）
   - 添加年份限制（2025 或 2026）
   - 使用引号精确匹配关键词

2. **执行搜索**
   - 使用 `web_search` 工具
   - 设置 `count=8` 获取足够的结果
   - 如需中文报告，设置 `language=zh`

3. **分析结果**
   - 提取报告标题、URL、来源站点
   - 识别权威性（Deloitte、McKinsey 等优先）
   - 过滤掉非 PDF 或非报告类结果

4. **返回给用户**
   - 列出 5-8 个最相关的报告pdf链接
   - 每个报告包含：标题、来源、年份、简短摘要（如有）
   - 推荐 3-5 个强相关的阅读链接（基于标题和来源权威性）

## 实用技巧

- **结果太多？** 加引号精确匹配，或添加 site: 限制
- **结果太少？** 去掉一些限制，如去掉 filetype:pdf 或 site:
- **想找互动/HTML 版？** 不加 filetype:pdf，或搜 `inurl:report -filetype:pdf`
- **时效性很重要**：优先加年份（如 2025、2026），旧报告参考价值较低
- **先用简单关键词搜一次**，看结果类型，再逐步添加运算符精炼

## 常见权威来源

**国际咨询公司：**
- Deloitte（德勤）
- PwC（普华永道）
- EY（安永）
- KPMG（毕马威）
- McKinsey（麦肯锡）
- BCG（波士顿咨询）

**中国机构：**
- 艾瑞咨询（iresearch.com.cn）
- 易观分析
- 艾媒咨询
- 中国国家统计局（stats.gov.cn）

**行业报告平台：**
- 发现报告（fxbaogao.com）
- 新研报
- 199IT
- Useit 知识库

## 注意事项

- SearXNG 可能不支持所有 Google 高级运算符（如 `after:`），优先使用 `filetype:pdf`、`site:`、`inurl:`、`""` 等通用运算符
- 部分报告可能需要注册或付费下载，在结果中标注
- 优先推荐 PDF 格式的正式报告，避免新闻稿或网页摘要
- 如果搜索结果质量不佳，尝试调整运算符组合或使用不同的关键词
