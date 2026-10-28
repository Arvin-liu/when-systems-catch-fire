# 104 Anysearch 使用文档

## 端点
- URL: `https://api.anysearch.com/v1/search`
- Method: POST
- Content-Type: application/json
- Authentication: 免 key（CORS 开放）

## 请求体
```json
{"query": "<检索式>", "limit": <N>}
```

## 响应体
```json
{
  "code": 0,
  "data": {
    "results": [
      {"title": "...", "url": "...", "snippet": "...", "content": "..."}
    ]
  }
}
```

## Smoke Test（2026-07-13 20:50 CST）
- Query: "causal inference survey 2024"
- Status: code=0, results=10
- Verified: Real titles returned, no errors

## 硬规则
1. **anysearch 仅用于线索发现（LEAD_DISCOVERED）**，不能作为论文存在、同行评审或内容支持的最终权威。
2. 任何从 anysearch 结果中提取的 DOI 必须再用 Crossref API 验真后才能入产物。
3. anysearch 返回的 content/snippet 不得直接用作论文摘要或结论。
4. 不得将 anysearch 返回结果直接称为"论文验证"。

## API Key 模式（未来）
- 当前免 key 模式已验证可用。
- 如需更高限额或更高质量结果，可能需要 API key。
- key 应通过环境变量 `ANYSEARCH_API_KEY` 配置，不得写入代码或 Git。
- key 缺失时安全降级到免 key 模式，不得伪造结果。
- `.env.example`:
  ```
  # Anysearch API Key (optional, free-key mode works without this)
  # ANYSEARCH_API_KEY=your_key_here
  ```

## 脚本位置
- 仓库内: `scripts/external-research/anysearch_client.py`
- 本地副本: `/tmp/088work/anysearch_client.py`（088 执行时）

## 调用示例
```bash
python3 scripts/external-research/anysearch_client.py "causal inference survey 2024" 5
```
