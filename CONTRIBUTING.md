# 贡献指南

仓库只有一个 skill：`skills/signal-codec/`。新增内容放进它的 `references/`，保持 `SKILL.md` 精简，只做路由。

## 新增模态

在 `references/decode/<modality>.md` 与 `references/encode/<modality>.md` 各加一份，并在 `SKILL.md` 的表格中加一行。两份文件互相独立；没有对应方向的能力就不写，不要用解码能力推断编码能力。

一份指南应回答：如何读取原始输入、如何选择算法、依赖和版本、如何运行、怎样让人或 LLM 看懂（解码），或怎样检查生成结果（编码）、原生输出怎样交给下一工具、如何发现失败。

## 新增外部 skill 或工具

写进 `references/external.md`，注明来源链接、核对日期、是否实测、需要的 key、数据是否上传。

## 规则

- 记录真实集成案例时，注明日期、版本、平台、命令、可公开的输入或合成数据、实际观察与失败条件。把“官方文档能力”“作者建议”“实测经验”分开写；未运行的例子不要写成已验证。
- 只在连接特定工具时定义局部适配。不要引入全仓库通用结果对象、强制 JSON envelope、统一 feature/event 字段或强制自然语言输出。
- 脚本放在 `skills/signal-codec/scripts/`，依赖尽量少，在脚本开头说明依赖，在小样本上运行验证。
- 生物信号只用于研究数据；RF 内容限离线分析与基带生成。

## 检查

```bash
python scripts/check_links.py                 # 仓库内 Markdown 链接
python skills/signal-codec/scripts/probe.py <file>   # 脚本烟雾测试
```

`SKILL.md` frontmatter 用 skill-creator 的 `quick_validate.py` 验证。
