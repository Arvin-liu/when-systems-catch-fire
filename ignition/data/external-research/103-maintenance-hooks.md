# 103 固化与可维护

## 续跑入口
阶段4 补某 gap：子代理已验真者直接采用；否则重跑 /tmp/088work/crossref_search_all.py <GAP-XXX>

## 更新协议
新增外部来源须经 Crossref 验真 → 更新 090/091/092 → 重算 097 tier → 校验 101 闸门。

## 红线（不可绕过）
- 不新增 Ψ₀ 函数编号
- 不改 Ψ₀:= 定义
- 不注入未验真外部理论
- MEDIUM 增强不修改现有判定结构

分支：records/ignition-088-external-literature-gap-source-atlas-20260713（未动 main，合并需用户授权）

## 联网检索通道（新增，已验证可用）
- `scripts/external-research/anysearch_client.py`：POST https://api.anysearch.com/v1/search，字段 `{"query","limit"}`，免 key、CORS 开放。
- 用途：解决先前 web_fetch 因 DNS/IP 限制不可用的问题；作为「找线索」通道。
- **闭环规则（反幻觉）**：anysearch 仅提供检索线索（title/url/snippet/content）；从中抽取的 DOI 必须再用 Crossref 双向核验（`curl -s "https://api.crossref.org/works/<DOI>"`）确认为真实后，才允许写入 088 产物。
- 合规边界：第三方免 key API，来源不明；结果不得直接采信，仅作线索。
