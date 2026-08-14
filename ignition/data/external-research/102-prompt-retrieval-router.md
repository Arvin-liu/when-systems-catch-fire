# 102 提示层与检索路由

- 路由规则：检索外部理论时，先按 gap_id 路由到对应 object_type 接口与已验真来源；无对应验真源则拒答并提示补全。
- 提示注入点：096-clm-alignment-layer-v2, 094-088-patch-library
- 已建 gap→source 路由条目数：8
