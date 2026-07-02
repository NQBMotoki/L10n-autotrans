<div align="center">

<a href="README.md">English</a> ｜
<a href="README.zh-CN.md">简体中文</a>

</div>

# L10n-autotrans

中文产品文案多语言本地化生成与 QA 工具。项目基于 Streamlit 构建，面向产品运营、App 出海运营、电商出海文案团队，用于批量输入中文文案，生成英语、日语、法语本地化版本，并自动输出基础 QA 报告。

本项目定位为作品集 Demo，不包含账号、权限、数据库等企业级系统，重点展示清晰的产品流程、模块化代码结构和可本地运行的 AI 应用能力。

## 功能亮点

- 批量输入中文文案，支持网页表格编辑、CSV / Excel 上传。
- 支持英语 `en`、日语 `ja`、法语 `fr` 多选，一次生成多语言结果。
- 根据文案类型动态调整 QA 关注点。
- 接入 DeepSeek API，并支持无 API Key 的 mock 演示模式。
- 自动检查长度风险、术语一致性、文化适配和语气风险。
- 支持导出 CSV、Excel、JSON。

## 技术栈

- Python
- Streamlit
- pandas
- requests
- python-dotenv
- openpyxl

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

启动后在浏览器中打开 Streamlit 输出的本地地址。

## `.env` 配置

复制 `.env.example` 为 `.env`，并按需填写：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

如果 `.env` 中没有 API Key，也可以在 Streamlit 侧边栏临时输入。临时输入的 Key 只保存在当前 session，不会写入本地文件。侧边栏提供“清除当前 API Key”按钮。

## DeepSeek API Key 说明

有 API Key 时，关闭 mock 模式即可调用 DeepSeek OpenAI-compatible Chat Completions 接口。模型输出被要求为严格 JSON，程序会解析 `localized_text`、`rationale`、`cultural_adaptation`、`tone_notes`、`risk_notes` 字段。

如果 API 不可用，应用会回退到 mock 示例结果，方便继续演示完整流程。

## Mock 模式

mock 模式不需要任何 API Key。它会返回示例本地化结果和 QA 说明，适合课堂展示、作品集录屏和离线评审。

## 输入表格格式

最低支持以下列：

```csv
id,source_text,copy_type,max_chars,ui_width_px
btn_001,立即购买,App 按钮,12,120
```

字段说明：

- `id`：文案编号，可选。
- `source_text`：中文原文，必填。
- `copy_type`：文案类型，可选；为空时使用页面默认文案类型。
- `max_chars`：最大字符数，可选。
- `ui_width_px`：UI 控件宽度，单位 px，可选。

示例文件位于 `sample_data/sample_input.csv`。

## 术语表格式

最低兼容格式：

```csv
source_term,target_term
会员,Membership
```

推荐格式：

```csv
source_term,target_language,target_term,note
会员,en,Membership,Use for subscription membership context
会员,ja,メンバーシップ,
会员,fr,abonnement,
```

上传后可在侧边栏自定义字段映射。如果术语表没有 `target_language` 列，需要手动选择这份术语表对应的目标语言。

示例文件位于 `sample_data/sample_terms.csv`。

## 导出结果

每条中文文案、每种目标语言会生成一条结果，包含：

- 原文与文案类型
- 目标语言与本地化译文
- 译法说明、文化适配建议、语气说明、风险说明
- 长度风险等级与原因
- 术语一致性状态
- `overall_status`：`pass`、`warning`、`fail`

页面支持导出为 CSV、Excel、JSON。

## 项目结构

```text
L10n-autotrans/
  app.py
  requirements.txt
  .env.example
  README.md
  README.zh-CN.md
  sample_data/
    sample_input.csv
    sample_terms.csv
  src/
    __init__.py
    llm_client.py
    prompts.py
    qa_rules.py
    terminology.py
    exporters.py
    schemas.py
    utils.py
```

## 作品集展示亮点

- 有明确用户场景：出海产品和电商文案本地化。
- 有可交互 Demo：无需 API Key 也能完整跑通。
- 有工程化拆分：页面、模型调用、Prompt、QA、术语、导出分层清晰。
- 有基础错误处理：API 异常、CSV 格式错误、JSON 解析失败不会导致整页崩溃。
- 有真实业务判断：不同文案类型对应不同 QA 关注点。

## 后续扩展方向

- 增加更多目标语言和地区变体，如 `en-US`、`en-GB`、`fr-CA`。
- 支持术语近似匹配、大小写检查、品牌名保护和多译法管理。
- 增加批量重试、缓存、成本统计和调用日志。
- 引入更细的 UI 长度估算，例如按字体、字号、组件类型计算。
- 支持人工审校状态、备注和二次改写。
- 增加 pytest 单元测试与 CI 检查。
