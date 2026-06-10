# behance-grab

下载、整理、检查并打包公开的 Behance 项目或情绪板链接。

## 概述

`behance-grab` 是一个用于本地归档和参考的 Behance 抓取 skill，支持：

- 下载单个公开 Behance 项目到你指定的文件夹
- 下载或增量更新公开 Behance 情绪板
- 检查项目或情绪板是否有更新
- 将已有下载目录打包为 ZIP
- 在正式下载前先测试 Behance 网络连通性

这个 skill 会保持情绪板项目顺序稳定，按数字顺序命名图片，并保留更新所需的元数据，方便后续增量检查。

## 用法

直接使用 skill 目录里的脚本：

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py <command>
```

### 常用命令

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py project "<project-url>" --output "<folder>" --zip
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py moodboard "<moodboard-url>" --output "<folder>" --zip
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py check "<url>" --output "<existing-folder>"
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py probe --remind
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py zip "<folder>"
```

### 命令说明

| 命令 | 作用 |
| --- | --- |
| `project` | 下载单个公开 Behance 项目。 |
| `moodboard` | 下载或增量更新公开 Behance 情绪板。 |
| `check` | 检查本地下载内容是否有远端更新。 |
| `probe` | 检测当前机器是否能连通 Behance。 |
| `zip` | 将已有下载目录打包成 ZIP。 |

## 安装

### 安装到 Codex

把整个目录复制到：

```text
C:\Users\lenovo\.codex\skills\behance-grab
```

然后重新启动或刷新 Codex，让它加载新的 skill 文件。

### 安装到其他 Agent

对于支持本地 skills、custom instructions 或工具包的其他 Agent，把同样的目录结构复制到对应的 skill 或自定义提示目录中，然后重新加载该 Agent。需要保留这些文件：

- `SKILL.md`
- `README.md`
- `scripts/behance_grab.py`
- `agents/openai.yaml`

## 注意事项

- Behance 素材通常受版权保护。
- 使用前应取得权利人许可，并遵守当地法律。
- 脚本依赖 `curl.exe`。
- 脚本使用了更长的超时和更多重试，以减少慢网络下的误失败。
- 开始下载前，skill 会先要求确认版权提示和输出目录。
