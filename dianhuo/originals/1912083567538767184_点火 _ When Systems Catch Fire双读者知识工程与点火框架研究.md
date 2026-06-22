# 《点火 / When Systems Catch Fire》：双读者知识工程与点火框架研究

### **📚 项目核心定位**

**本质属性**：这不是简单托管在GitHub上的书稿，而是一个**Agent-readable book project**（AI代理可读的书籍项目）和**AI-readable open knowledge repository**（AI可读的开放知识仓库）。

**核心目标**：研究关键人物在关键时期通过关键动作改变系统燃烧条件，使新系统被应约者接住、延迟接住、错误接住或无法接住的历史结构，探索"制度、资源、技术、流程都已搭好后，为何有些系统真正活起来"的核心问题。

### **👥 双读者设计**

| 读者类型 | 核心入口 | 内容形式 | 阅读目标 |
| :------- | :------- | :------- | :------- |
| **人类读者** | `SUMMARY.md`、`book/`目录 | 正文叙述、章节结构 | 理解"点火框架 / Ignition Framework"理论 |
| **AI Agent读者** | `llms.txt`、`llms-full.txt`、`agent/`、`data/` | 结构化概念、论点、案例、证据、待解决问题 | 快速读取、检索、引用、改写和执行任务 |

### **🔑 核心命名体系**

| 元素 | 名称 | 说明 |
| :--- | :--- | :--- |
| **Book title** | **When Systems Catch Fire** | 英文书名 |
| **中文书名** | **点火** | 中文正式名称 |
| **Core theory** | **Ignition Framework / 点火框架** | 本书使用和发展的核心理论名 |
| **Repository** | **when-systems-catch-fire** | GitHub仓库名，保持固定不更改 |

### **📝 理论核心摘要**

**点火框架（Ignition Framework）** 研究新秩序如何形成，区分两类系统：
- **协作系统（collaboration system）**：构建制度、流程、组织、资源和技术结构
- **识别系统（recognition system）**：决定应约者是否愿意进入并将新秩序视为己有

**核心问题**：不仅关注系统能否运行，更关注在压力下必须决定是否进入系统的人们能否认可它。

### **📂 仓库结构解析**
```
book/      正式书稿整理层，面向人类读者
agent/     AI Agent友好的摘要、概念、论点、案例、术语和问答路径
data/      结构化数据，目前包括ignition case CSV
dianhuo/   原始书稿、框架笔记、证据材料和归档内容
SUMMARY.md 全书目录
llms.txt   AI Agent简短入口
llms-full.txt AI Agent一次性读取入口
```
### **⏱️ 当前项目状态**
- **版本性质**：非破坏性整理稿，`book/`中为基于现有目录、框架笔记和案例线索的工作稿
- **AI材料**：`agent/`中的材料用于检索、引用、重组和任务执行
- **历史保留**：原有`dianhuo/`内容未删除，作为来源层和后续扩写材料
- **最新更新**：2026-06-06新增事件框架版增量，包括：
  - `dianhuo/02-framework/`下的事件框架相关文件
  - `dianhuo/01-manuscript/`中的章节结构文件
  - `dianhuo/03-evidence/cases/all-cases-71.md`案例文件
  - `data/`目录下的事件规模矩阵和点火案例CSV文件
> **注意**：当前新增内容为工作稿和待核查案例表，不应视为已完成史实证明。

### **📜 许可协议条款**

**核心协议**：**Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License**（知识共享署名—非商业性使用—相同方式共享4.0国际许可协议，简称CC BY-NC-SA 4.0）

**使用条件**：
1. **署名（Attribution）**：必须保留作者署名与原始仓库链接
2. **非商业（NonCommercial）**：不得用于商业目的
3. **相同方式共享（ShareAlike）**：改编创作需采用相同或兼容许可协议
4. **不得暗示背书（No endorsement）**：不得暗示原作者认可改编版本

**项目性质**：非商业开放内容项目，而非OSI意义上的软件开源项目（因禁止商业使用）

### **补充细节**
- **创新形式**：本项目将书籍改造成能被人类和AI同时读取、引用、重组、传播和继续生长的系统，超越了简单的"书稿托管"模式
- **内容分类**：采用"整理层（book）-来源层（dianhuo）-AI交互层（agent）-数据层（data）"的四维结构，实现内容的多维度利用
- **动态发展**：通过GitHub的版本化管理，使理论框架和案例库能够持续迭代和扩展
