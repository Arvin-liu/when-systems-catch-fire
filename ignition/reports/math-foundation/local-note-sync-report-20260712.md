# Local Note Sync Report

> 076 correction notice: this is a preserved 075 filesystem snapshot. A fresh read-only check found /Users/zhiyuan/我的笔记/getnote-notes present with 117986 files, while /Users/zhiyuan/我的笔记/得到大脑 remained absent. Current evidence is recorded in reports/foundation-architecture/local-source-recovery-audit-20260712.md. Directory existence alone does not verify per-object provenance.

## Scope

- `/Users/zhiyuan/Documents/GetNoteVault/getnote-notes`: exists=no
- `/Users/zhiyuan/我的笔记/得到大脑`: exists=no
- `/Users/zhiyuan/我的笔记/2026-07-09 1735`: exists=yes
  files=141, latest_mtime=2026-07-09 17:36:06, sampled_total_size_bytes=135155
- `/Users/zhiyuan/我的笔记/2026-07-09 1902`: exists=yes
  files=41, latest_mtime=2026-07-09 19:03:04, sampled_total_size_bytes=140294

## Sync Result

- 本轮未调用得到大脑进行数学判断、理论修正或函数重写。
- 仅对本地可见目录做只读覆盖检查和哈希抽样。
- `/Users/zhiyuan/Documents/GetNoteVault/getnote-notes` 与 `/Users/zhiyuan/我的笔记/得到大脑` 当前缺失，纳入 blocker。
- `2026-07-09 1735` 与 `2026-07-09 1902` 目录存在，可作为局部来源补充。

## Hash Sample

### /Users/zhiyuan/我的笔记/2026-07-09 1735
- `12个元协议重新验证21本书 2026年7月9日16_42__1915111478682489032.md` sha256 `c193841984c3e60c95049a0b26bce6e05b95eeee4cf67481acde313f6ddf7faf`
- `21本书哥德尔不完备性元层面收敛尝试 2026年7月9日16_25__1915110328703812464.md` sha256 `88e138e553ec42cf29b5832e5644756fe0a4eaff59796dad791990d9070c6936`
- `Afford-VLA：面向机器人操作的动作对齐型内部化视觉规划框架深度解析__1915114685947609968.md` sha256 `b111a824fe260f24c05d545cc715feed04de42c2a8d6c8d502d6c3731a72c82b`
- `OpenAI GPT-Live 技术发布深度解析：AI语音交互迈入全双工实时对话新时代__1915102101693042888.md` sha256 `91e010cb916f890e810d09239158258282372863fc59a57ab9369afc0ef5fa8b`
- `untitled__1915114533475746672.md` sha256 `fca459ede0ddbe957bc9b20481bcfb0d70a30e7c2d363897e109f41b2a09fce0`
- `《乌合之众》最终收敛报告 2026年7月9日15_47__1915107939628778352.md` sha256 `8b8ca8654e251baacd9d941b89fbfbd57304f79bbb84f09f68bcd6c1629afd9c`
- `《乌合之众》第一轮验证报告 2026年7月9日15_45__1915107833326764912.md` sha256 `19f40c47dee77d61691a4ea340361b461d1ad8d80a1776298915957f884a578a`
- `《乌合之众》第三轮执行报告 2026年7月9日15_47__1915107910638273392.md` sha256 `5169b2fcee7b3d93d44dc5e0c716c0cacbfd7d885c8b0fdfdef7577263c186a0`
- `《乌合之众》第二轮执行报告 2026年7月9日15_46__1915107868760769392.md` sha256 `e6baaecda9fbd3e80504178fe4ac81a3c07559b07d9d6722bf737ecf6f6b441f`
- `《人类简史》最终收敛报告 2026年7月9日15_37__1915107251358620248.md` sha256 `e65e8ba9ff533e70e48d2b6221284f6b4001f7e8f2ecd2445ca14df980c2be04`

### /Users/zhiyuan/我的笔记/2026-07-09 1902
- `2026年7月9日点火框架书籍验证总数检查报告 2026年7月9日18_10__1915117231789474672.md` sha256 `cf2016c53e892ded081d7397e550dca2a435ef64446c206ab0e46e3948ce8036`
- `2026年7月9日点火框架书籍验证总数检查报告（修正版） 2026年7月9日18_13__1915117431508209864.md` sha256 `a4eb511d5cdc9b2f4a0ea354ec20bc59418a92096acdf304a54a0e60faeb1df6`
- `22本书籍验证案例清单（元协议重跑版） 2026年7月9日18_20__1915117838454264008.md` sha256 `12d86902fb071b291e56430ed1a252015e999fa7148f8fac6f31af79398c366f`
- `E₁ 线性演化协议 64种可能性 2026年7月9日18_37__1915119239687344328.md` sha256 `5df5d35a9a6b6941bdd92548c9e96f4a7d3e897bbd5a2641450e600dff951b34`
- `E₂ 非线性演化协议 64种可能性 2026年7月9日18_37__1915119409337817688.md` sha256 `5d41a62a47330ef3d70ba7cc0c51d2a71668d1be3f3330eb674d715e541efe86`
- `E₃ 循环演化协议 64种可能性 2026年7月9日18_37__1915119409338341976.md` sha256 `80c246ffb8924ccb91d6997b58ccf0b0e751eaacba6d63ff8061867d898cc2df`
- `E₄ 收敛演化协议 64种可能性 2026年7月9日18_37__1915119409338866264.md` sha256 `949353f8244082f778816e72a369841591c412318c32f99f67f4ab2309f65290`
- `S₁ 封闭边界协议 64种可能性 2026年7月9日18_37__1915119161303481824.md` sha256 `59c0b74522779f551a42d0ec3747014647cba40255799004f1d23c615abdd374`
- `S₂ 开放边界协议 64种可能性 2026年7月9日18_37__1915119161304006112.md` sha256 `3270b20f6d21634ba1127f54c73e13d2124a0317fcd9af63b989b6815a409b84`
- `S₃ 层级协议 64种可能性 2026年7月9日18_37__1915119161304530400.md` sha256 `139bb5a6aafc75d6bba8206f1aab21990eb95af46442c6386971ca6fe558ca38`

## Coverage Assessment

- 当前可确认落地覆盖到 2026-07-09 的两批本地导出目录。
- 默认 Obsidian/得到大脑正文源目录在本机当前不可见，因此无法声明连续覆盖。
- 同步失败不阻断 075，其影响已转入 blocker 与 provenance 缺口状态。
