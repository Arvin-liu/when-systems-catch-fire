# Publication Reader MVP

本目录是一个可本地预览的静态读者前端。

## 预览方式

在仓库根目录执行：

```bash
python3 -m http.server 8080 --directory outputs/publication-reader-mvp
```

然后打开：

```text
http://127.0.0.1:8080/
```

## 说明

- 数据直接读取 `data/publication-atlas-20260712.json`
- 只做浏览、筛选、证据跳转
- 不包含构建工具、不包含脚手架、不修改正文结论
