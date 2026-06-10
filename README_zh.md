[English](README.md) | 中文

# behance-grab

下载、整理、检查并打包公开的 Behance 项目或情绪板链接。

## 功能

- 下载单个公开 Behance 项目到指定文件夹。
- 下载或增量更新公开 Behance 情绪板。
- 检查项目或情绪板是否有更新。
- 将已下载的项目或情绪板打包为 ZIP。
- 在开始下载前先测试 Behance 是否可达。

## 用法

使用内置脚本：

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py <command>
```

常用命令：

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py project "<project-url>" --output "<folder>" --zip
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py moodboard "<moodboard-url>" --output "<folder>" --zip
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py check "<url>" --output "<existing-folder>"
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py probe --remind
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py zip "<folder>"
```

## 安装

### Codex

把整个技能目录复制到：

```text
C:\Users\lenovo\.codex\skills\behance-grab
```

然后重新启动或刷新 Codex，让它加载新的 skill 文件。

### 其他 Agent

对于支持本地技能、定制指令或工具包的其他 Agent，把相同的目录结构复制到对应的 skill 或自定义提示目录里，然后重新加载该 Agent。请保持这些文件在一起：

- `SKILL.md`
- `README.md`
- `README_zh.md`
- `scripts/behance_grab.py`
- `agents/openai.yaml`

## 注意

- Behance 素材通常受版权保护。
- 仅在获得权利人许可并遵守当地法律的前提下使用。
- 脚本依赖 `curl.exe`，并且使用了更长的超时和重试设置，以适应较慢网络。
