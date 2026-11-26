# QA Test Vault Workflow

一个把「需求 → 需求梳理 → 测试点 → 测试用例 → 冒烟用例 → xmind」整条链路固化下来的 Agent Skill。适用于用 Obsidian / Markdown 按 release 迭代管理测试资产的团队，也可以直接当作个人测试知识库的工作规范。

Skill 名：`qa-test-vault-workflow`

## 解决什么问题

测试资产最容易出的问题不是"写得少"，而是：

- 需求没确认就开写，用例建立在猜测上
- 测试点没有出处，需求一改无法追溯
- 为了"精简"删掉边界和负向断言，缺陷从缝里漏过去
- 测试点、用例、xmind 三份文件各说各话

这个 Skill 把门禁、出处、断言强度写成硬约束，让 Agent 按同一套规则产出和审核。

## 工作流

```
需求输入（PRD / 原型 / 流程图 / 历史 xmind）
   ↓
① 需求梳理 → 需求.md + A/B/C/D 确认点
   ↓  ← 门禁：等需求方确认
② 回填确认结果
   ↓
③ 测试点 → 测试点.md          ← 门禁：完成即停
   ↓  ← 门禁：用户明确说「生成测试用例」
④ 测试用例 → 测试用例.md      ← 门禁：完成即停
   ↓  ← 门禁：用户明确说「生成冒烟用例」
⑤ 冒烟用例 → 冒烟测试用例.md  ← 门禁：完成即停
   ↓  ← 门禁：用户明确说「转 xmind」
⑥ xmind 导出
```

四道门禁独立触发，不合并、不越级。"继续/好的"不视为授权。

## 目录结构

```
qa-test-vault-workflow/
├── SKILL.md
├── references/
│   ├── vault-conventions.md        # 目录、命名、frontmatter、附件、归档
│   ├── requirements.md             # 需求梳理、确认点、确认回填
│   ├── test-points.md              # 四层结构、编号、出处、覆盖维度、禁止项
│   ├── test-cases-and-smoke.md     # 用例与冒烟标准
│   └── review-and-answers.md       # 审核报告、答疑格式、执行记录
├── assets/templates/
│   ├── 需求模板.md
│   ├── 测试点模板.md
│   ├── 测试用例模板.md
│   ├── 冒烟测试用例模板.md
│   ├── 测试点审核报告模板.md
│   └── 执行记录模板.md
└── scripts/
    └── md2xmind.py                 # 测试点/用例 md → XMind（Zen 格式）
```

## 安装

Qoder 用户级（所有项目可用）：

```bash
git clone <本仓库地址> cyy-skills
cp -r cyy-skills/skills/qa-test-vault-workflow ~/.qoder/skills/
```

项目级（只对当前仓库生效）：

```bash
mkdir -p .qoder/skills
cp -r cyy-skills/skills/qa-test-vault-workflow .qoder/skills/
```

也可以用 skills CLI 安装（仓库公开后）：

```bash
npx skills add <你的GitHub用户名>/cyy-skills@qa-test-vault-workflow -y
```

安装后重开会话，或执行 `/skills reload`，用 `/qa-test-vault-workflow` 调用。

## 触发示例

- "把 `_收件箱/` 里这份 PRD 梳理一版需求，列出确认点"
- "确认点都按建议默认，生成测试点"
- "测试点写得怎么样，先审核一下再生成用例"
- "生成冒烟用例"
- "把测试点转成 xmind"
- "发帖时标签是不是只能选 3 个？"（需求口径答疑：结论 → 出处 → 易混点）

## 设计原则

1. **门禁优先**：每份产物完成即停，等明确指令，防止一路自动生成到用例。
2. **md 是唯一事实源**：xmind 由脚本从 md 生成；手工改 xmind 后必须回写并 diff。
3. **出处可追溯**：每条测试点必须落到 PRD 章节、AC、批注号或确认点。
4. **不弱化断言**：具体阈值、负向断言、只读限制是测试点的价值，不允许以精简为名删除。
5. **通用化**：不绑定具体项目、公司系统或字段；vault 根目录自动探测，模板用占位符。

## 环境要求

- Python 3.6+（仅 xmind 导出脚本需要，无第三方依赖）
- XMind 2020+ 打开导出文件；旧版 XMind 8 会提示版本过低
- Obsidian 可选，frontmatter 用于全文检索与过滤

## 适配自己的知识库

- 目录、编号、frontmatter 约定见 `references/vault-conventions.md`，按团队习惯改这一份即可。
- `type` 字段支持中英文两套取值，以 vault 内既有为准，不要混用。
- 编号体系（`TP-A01-01`、`TC-01`、`TC-S-01`）可按团队规范调整，但要保持同一需求内一致。

## 说明

本 Skill 是通用工作流，不包含任何公司内部系统、项目名、提单模板或账号信息。如果你有自己的需求单/缺陷单模板，放在 `assets/templates/` 下并在 SKILL.md 中引用即可。
