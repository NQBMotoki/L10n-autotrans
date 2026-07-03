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
- 支持轻量多 Provider：Mock、DeepSeek、OpenAI / ChatGPT、Anthropic / Claude、OpenRouter。
- 自动检查长度风险、术语一致性、文化适配和语气风险。
- API 调用失败时可自动回退到 Mock，方便作品集演示不中断。
- 支持导出 CSV、Excel、JSON，并保留 provider 与 model 信息。

## 技术栈

- Python
- Streamlit
- pandas
- requests
- python-dotenv
- openpyxl
- openai
- anthropic

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

启动后在浏览器中打开 Streamlit 输出的本地地址。

## `.env` 配置

复制 `.env.example` 为 `.env`，并按需填写：

```env
# Default provider used when the app starts.
# Valid values: mock, deepseek, openai, anthropic, openrouter
DEFAULT_PROVIDER=mock

# DeepSeek
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_DEFAULT_MODEL=

# OpenAI / ChatGPT API
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_DEFAULT_MODEL=

# Anthropic / Claude API
ANTHROPIC_API_KEY=
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_DEFAULT_MODEL=

# OpenRouter
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_DEFAULT_MODEL=
OPENROUTER_SITE_URL=
OPENROUTER_APP_NAME=L10n-autotrans
```

`DEFAULT_PROVIDER` 控制应用启动时默认选择的 Provider。如果没有配置或配置错误，会回退到 `mock`。

## 支持的 LLM Provider

侧边栏每次运行只能选择一个 Provider：

- Mock
- DeepSeek
- OpenAI / ChatGPT
- Anthropic / Claude
- OpenRouter

目标语言仍然支持多选，因此一个 Provider 可以在同一次批处理中生成英语、日语、法语结果。

## 模型配置

模型名称可能随时间变化。不要把示例或旧模型名视为永久有效。建议使用应用内的 “Refresh models” 按钮，或参考 Provider 官方文档选择当前可用模型。

每个真实 Provider 都有模型下拉框和 `Manual model override` 输入框。如果模型列表刷新失败，仍可以手动粘贴有效模型名。如果没有任何可用模型名，应用会阻止真实 API 调用，并提示刷新模型、手动输入模型名，或切换到 Mock。

## API Key 处理

API Key 可以从 `.env` 读取，也可以在 Streamlit 页面临时输入。临时输入的 API Key 只保存在当前 Streamlit session，不会写入本地文件。UI 只会显示当前所选真实 Provider 对应的 API Key 输入框。

Mock 不需要 API Key。真实 Provider 如果没有可用 API Key，应用会提示输入 API Key 或切换到 Mock。

## Mock 模式与 fallback

mock 模式不需要任何 API Key。它会返回示例本地化结果和 QA 说明，适合课堂展示、作品集录屏和离线评审。

开启 “Fallback to Mock when API call fails” 后，真实 Provider 调用失败会自动回退到 Mock 结果。导出文件中包含 `provider`、`model`、`provider_status` 字段，便于离开网页后仍能知道结果来源。

代码中已提供 DeepSeek、OpenAI / ChatGPT、Anthropic / Claude、OpenRouter 的 API 调用路径，但实际可用性取决于你自己的 API Key、模型名和 Provider 侧权限。

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
- Provider、model 和 provider status
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
- 有工程化拆分：页面、多 Provider 模型调用、Prompt、QA、术语、导出分层清晰。
- 有基础错误处理：API 异常、CSV 格式错误、JSON 解析失败不会导致整页崩溃。
- 有真实业务判断：不同文案类型对应不同 QA 关注点。

## 后续扩展方向

- 增加更多目标语言和地区变体，如 `en-US`、`en-GB`、`fr-CA`。
- 支持术语近似匹配、大小写检查、品牌名保护和多译法管理。
- 增加批量重试、缓存、成本统计和调用日志。
- 增加自定义 OpenAI-compatible Provider 或轻量 Provider 注册机制。
- 引入更细的 UI 长度估算，例如按字体、字号、组件类型计算。
- 支持人工审校状态、备注和二次改写。
- 增加 pytest 单元测试与 CI 检查。
