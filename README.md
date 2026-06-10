# behance-grab

用于下载、整理、检查并打包公开 Behance 项目或情绪板的 Agent Skill 工具。

## 概述

`behance-grab` 是一个面向本地归档、设计参考与素材整理场景的 Behance 抓取工具。它可以帮助你将公开的 Behance 项目或情绪板下载到本地，并保留必要的元数据，方便后续检查更新、增量同步和打包归档。

该工具适合配合 Codex、Claude Code、Cursor、Windsurf 等 Agent 使用，也可以直接作为命令行脚本独立运行。

## 功能特性

* 下载前自动检测当前环境是否可以访问 Behance
* 下载单个公开 Behance 项目到指定目录
* 下载或增量更新公开 Behance 情绪板
* 检查本地项目或情绪板是否存在远端更新
* 将已有下载目录打包为 ZIP 文件
* 保持情绪板项目顺序稳定
* 按数字顺序命名图片，便于浏览、引用和归档
* 保留更新所需的元数据，方便后续增量检查

## 目录结构

建议目录结构如下：

```text
behance-grab/
├─ SKILL.md
├─ README.md
└─ scripts/
   └─ behance_grab.py
```

其中：

* `SKILL.md`：给 Agent 读取的技能说明文件。
* `README.md`：给用户阅读的使用说明。
* `scripts/behance_grab.py`：实际执行下载、检查和打包的脚本。

## 用法

在 skill 目录中执行脚本：

```powershell
python <skill-root>\scripts\behance_grab.py <command>
```

其中 `<skill-root>` 指 `behance-grab` 所在目录。

## 常用命令

### 下载单个 Behance 项目

```powershell
python <skill-root>\scripts\behance_grab.py project "<project-url>" --output "<folder>" --zip
```

### 下载或增量更新 Behance 情绪板

```powershell
python <skill-root>\scripts\behance_grab.py moodboard "<moodboard-url>" --output "<folder>" --zip
```

### 检查远端是否有更新

```powershell
python <skill-root>\scripts\behance_grab.py check "<url>" --output "<existing-folder>"
```

### 测试 Behance 连通性

```powershell
python <skill-root>\scripts\behance_grab.py probe --remind
```

### 打包已有下载目录

```powershell
python <skill-root>\scripts\behance_grab.py zip "<folder>"
```

## 命令说明

| 命令          | 作用                     |
| ----------- | ---------------------- |
| `project`   | 下载单个公开 Behance 项目。     |
| `moodboard` | 下载或增量更新公开 Behance 情绪板。 |
| `check`     | 检查本地已下载内容是否存在远端更新。     |
| `probe`     | 检测当前机器是否可以连通 Behance。  |
| `zip`       | 将已有下载目录打包为 ZIP 文件。     |

## 安装方式

### 方式一：安装到 Codex

将整个 `behance-grab` 目录复制到 Codex 的 skills 目录中：

```text
<CODEX_HOME>/skills/behance-grab
```

安装后目录示例：

```text
<CODEX_HOME>/skills/
└─ behance-grab/
   ├─ SKILL.md
   ├─ README.md
   └─ scripts/
      └─ behance_grab.py
```

然后重新启动或刷新 Codex，让它重新加载 skill。

安装完成后，可以对 Codex 说：

```text
使用 behance-grab 下载这个 Behance 项目，并打包为 ZIP。
```

或者：

```text
检查我之前下载的这个 Behance 情绪板有没有更新。
```

### 方式二：安装到 Claude Code

如果使用 Claude Code，可以将 `behance-grab` 放到项目级技能目录中：

```text
<project-root>/.claude/skills/behance-grab
```

安装后目录示例：

```text
<project-root>/
└─ .claude/
   └─ skills/
      └─ behance-grab/
         ├─ SKILL.md
         ├─ README.md
         └─ scripts/
            └─ behance_grab.py
```

Claude Code 会根据 `SKILL.md` 中的说明，在相关任务中自动选择该 skill，或者你可以明确要求它使用该工具。

示例指令：

```text
请使用 behance-grab 下载这个公开 Behance 情绪板，保存到 ./references/behance，并打包。
```

### 方式三：接入 Cursor

Cursor 更适合通过项目规则或 `AGENTS.md` 方式接入该工具。

推荐做法：

1. 将 `behance-grab` 目录放到项目的工具目录中，例如：

```text
<project-root>/tools/behance-grab
```

2. 在项目根目录创建或更新 `AGENTS.md`：

````md
# Project Agent Instructions

本项目可以使用本地工具 `tools/behance-grab` 下载、检查和打包公开 Behance 项目或情绪板。

当用户要求下载 Behance 项目、整理 Behance 情绪板、检查更新或打包 Behance 素材时，优先使用：

```powershell
python tools\behance-grab\scripts\behance_grab.py <command>
````

使用前必须提醒用户：

* Behance 素材通常受版权保护；
* 下载内容仅用于本地归档、研究或设计参考；
* 商业使用前应取得权利人许可；
* 执行下载前需要确认输出目录。

````

3. 如果使用 Cursor Rules，也可以将相同内容写入：

```text
<project-root>/.cursor/rules/behance-grab.mdc
````

这样 Cursor Agent 在处理 Behance 下载相关任务时，就能知道如何调用该脚本。

### 方式四：接入 Windsurf

Windsurf 可以通过 Rules 方式接入该工具。

推荐做法：

1. 将 `behance-grab` 目录放到项目工具目录：

```text
<project-root>/tools/behance-grab
```

2. 在 Windsurf 的 Workspace Rules 中加入说明：

````md
当用户要求下载、整理、检查或打包公开 Behance 项目/情绪板时，使用本项目中的 behance-grab 工具：

```powershell
python tools\behance-grab\scripts\behance_grab.py <command>
````

可用命令：

* project：下载单个公开 Behance 项目
* moodboard：下载或增量更新公开 Behance 情绪板
* check：检查远端更新
* probe：测试 Behance 连通性
* zip：打包已有下载目录

执行前需要提醒用户确认版权提示和输出目录。

````

3. 保存规则后，在 Windsurf/Cascade 中直接描述任务即可，例如：

```text
用 behance-grab 下载这个 Behance moodboard，并保存到 references/board-a。
````

### 方式五：通用 Agent 接入方式

如果你的 Agent 不支持原生 Skill 目录，也可以按通用工具方式接入。

推荐结构：

```text
<project-root>/
├─ AGENTS.md
└─ tools/
   └─ behance-grab/
      ├─ SKILL.md
      ├─ README.md
      └─ scripts/
         └─ behance_grab.py
```

在 `AGENTS.md` 中加入：

````md
## behance-grab

本项目包含一个 Behance 下载与归档工具：

```powershell
python tools\behance-grab\scripts\behance_grab.py <command>
````

当用户提出以下需求时使用该工具：

* 下载公开 Behance 项目
* 下载公开 Behance 情绪板
* 检查 Behance 项目或情绪板是否有更新
* 将已下载的 Behance 素材目录打包为 ZIP
* 测试当前环境是否能访问 Behance

执行下载前必须：

1. 提醒用户 Behance 素材通常受版权保护；
2. 要求用户确认下载用途符合授权和当地法律；
3. 确认输出目录；
4. 优先运行 `probe` 检查连通性。

````

这种方式适合大多数支持读取项目说明文件的代码 Agent，例如通用 CLI Agent、IDE Agent、自建 Agent 或团队内部 Agent。

## 推荐工作流

### 第一次下载项目

```powershell
python <skill-root>\scripts\behance_grab.py probe --remind
python <skill-root>\scripts\behance_grab.py project "<project-url>" --output "<folder>" --zip
````

### 第一次下载情绪板

```powershell
python <skill-root>\scripts\behance_grab.py probe --remind
python <skill-root>\scripts\behance_grab.py moodboard "<moodboard-url>" --output "<folder>" --zip
```

### 后续检查更新

```powershell
python <skill-root>\scripts\behance_grab.py check "<url>" --output "<existing-folder>"
```

如果存在更新，再执行：

```powershell
python <skill-root>\scripts\behance_grab.py moodboard "<moodboard-url>" --output "<existing-folder>" --zip
```

## 输出说明

下载完成后，输出目录中通常会包含：

```text
<folder>/
├─ images/
│  ├─ 001.jpg
│  ├─ 002.jpg
│  └─ ...
├─ metadata.json
└─ manifest.json
```

说明：

* `images/`：下载后的图片文件。
* `metadata.json`：项目或情绪板的基础信息。
* `manifest.json`：用于检查更新和增量同步的文件清单。

如果使用 `--zip` 参数，还会生成对应的 ZIP 文件。

## 注意事项

* Behance 上的素材通常受版权保护。
* 本工具仅用于公开内容的本地归档、研究、灵感整理和设计参考。
* 商业使用、二次分发或公开发布前，应取得权利人许可。
* 使用前请遵守 Behance 平台规则以及当地法律法规。
* 下载前建议先运行 `probe` 命令确认网络连通性。
* 对于情绪板，建议保留 `metadata.json` 和 `manifest.json`，否则可能影响后续增量更新和检查。
