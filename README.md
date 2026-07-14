<div align="center">

<a href="README.md">English</a> ｜
<a href="README.zh-CN.md">简体中文</a>

</div>

# L10n-autotrans

A Multilingual Copy Localization QA Tool for Chinese product copy. Built with Streamlit, this project is designed for product operations, app global expansion teams, and cross-border ecommerce copy teams. It supports batch input of Chinese copy, generates localized versions in English, Japanese, and French, and automatically produces a basic QA report.

This project is positioned as a portfolio demo. It does not include enterprise-level account systems, permissions, or databases. Instead, it focuses on a clear product workflow, modular code organization, and a locally runnable AI application.

## Feature Highlights

- Batch input for Chinese copy, with editable web tables and CSV / Excel uploads.
- Multi-select target languages: English `en`, Japanese `ja`, and French `fr`.
- Dynamic QA focus based on copy type.
- Lightweight multi-provider support: Mock, DeepSeek, OpenAI / ChatGPT, Anthropic / Claude, and OpenRouter.
- Automated checks for length risk, terminology consistency, cultural adaptation, and tone risk.
- Mock fallback for failed API calls, so portfolio demos can continue even when a provider is unavailable.
- Export results as CSV, Excel, or JSON, including provider and model metadata.

## Tech Stack

- Python
- Streamlit
- pandas
- requests
- python-dotenv
- openpyxl
- openai
- anthropic

## Local Setup

```bash
python -m pip install --upgrade -r requirements.txt
streamlit run app.py
```

After startup, open the local URL printed by Streamlit in your browser.

The `--upgrade` flag is important for existing environments. OpenAI Python 1.55.3 or newer is
required for compatibility with HTTPX 0.28 and newer. If the app reports
`Client.__init__() got an unexpected keyword argument 'proxies'`, rerun the install command above
and restart Streamlit.

## `.env` Configuration

Copy `.env.example` to `.env` and fill in the values as needed:

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

`DEFAULT_PROVIDER` controls the provider selected when the app starts. If it is missing or invalid, the app falls back to `mock`.

## Supported LLM Providers

The sidebar lets you choose one provider per run:

- Mock
- DeepSeek
- OpenAI / ChatGPT
- Anthropic / Claude
- OpenRouter

Target languages remain multi-select, so one selected provider can generate English, Japanese, and French results in a single batch.

## Model Configuration

Model names may change over time. Do not treat example or old model names as permanently valid. Use the in-app "刷新模型列表" (Refresh model list) button or the provider's official documentation to select a current model.

Each real provider has a "模型" (Model) selector and a "手动指定模型" (Specify model manually) input. If the model list cannot be refreshed, you can still paste a valid model name manually. If no model name is available, the app blocks real API calls and asks you to refresh models, enter a model manually, or switch to Mock.

## API Key Handling

API keys can be loaded from `.env` or temporarily entered in the Streamlit UI. Temporary API keys are stored only in the current Streamlit session and are not written to local files. The UI shows only the API key input for the currently selected real provider.

Mock mode works without API keys. For real providers, if no API key is available, the app prompts you to enter one or switch to Mock.

## Mock Mode and Fallback

Mock mode does not require an API key. It returns sample localization results and QA notes, making it suitable for classroom demos, portfolio walkthroughs, and offline reviews.

When "API 调用失败时自动回退到 Mock" (Automatically fall back to Mock after an API failure) is enabled, failed real-provider calls automatically fall back to Mock results. Result exports include `provider`, `model`, and `provider_status` fields so exported files preserve the source of each result.

The code includes API call paths for DeepSeek, OpenAI / ChatGPT, Anthropic / Claude, and OpenRouter, but availability depends on your own valid API keys, model names, and provider-side access.

## Input Table Format

The minimum supported columns are:

```csv
id,source_text,copy_type,max_chars,ui_width_px
btn_001,立即购买,App 按钮,12,120
```

Field descriptions:

- `id`: Optional copy identifier.
- `source_text`: Required Chinese source text.
- `copy_type`: Optional copy type. If empty, the page-level default copy type is used.
- `max_chars`: Optional maximum character count.
- `ui_width_px`: Optional UI control width in pixels.

The sample file is located at `sample_data/sample_input.csv`.

## Terminology Table Format

Minimum compatible format:

```csv
source_term,target_term
会员,Membership
```

Recommended format:

```csv
source_term,target_language,target_term,note
会员,en,Membership,Use for subscription membership context
会员,ja,メンバーシップ,
会员,fr,abonnement,
```

After uploading a terminology table, you can customize the field mapping in the sidebar. If the table does not include a `target_language` column, you need to manually select which target language the table applies to.

The sample file is located at `sample_data/sample_terms.csv`.

## Exported Results

Each Chinese copy item and each target language generates one result row, including:

- Source text and copy type
- Target language and localized text
- Translation rationale, cultural adaptation suggestions, tone notes, and risk notes
- Provider, model, and provider status
- Length risk level and explanation
- Terminology consistency status
- `overall_status`: `pass`, `warning`, or `fail`

The page supports exporting results as CSV, Excel, and JSON.

## Project Structure

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

## Portfolio Highlights

- Clear user scenario: localization for global expansion products and ecommerce copy.
- Interactive demo: the full workflow runs without an API key through mock mode.
- Modular engineering structure: UI, multi-provider model calls, prompts, QA, terminology, and export logic are separated.
- Basic error handling: API errors, CSV format issues, and JSON parsing failures do not crash the whole page.
- Practical product judgment: different copy types map to different QA focus areas.

## Future Extensions

- Add more target languages and regional variants, such as `en-US`, `en-GB`, and `fr-CA`.
- Support fuzzy terminology matching, case checks, brand-name protection, and multi-translation management.
- Add batch retry, caching, cost tracking, and call logs.
- Add custom OpenAI-compatible providers or a lightweight provider registry.
- Introduce more detailed UI length estimation based on font, font size, and component type.
- Support human review status, reviewer notes, and second-pass rewriting.
- Add pytest unit tests and CI checks.
