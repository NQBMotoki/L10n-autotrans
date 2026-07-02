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
- DeepSeek API integration with a mock mode for demos without an API key.
- Automated checks for length risk, terminology consistency, cultural adaptation, and tone risk.
- Export results as CSV, Excel, or JSON.

## Tech Stack

- Python
- Streamlit
- pandas
- requests
- python-dotenv
- openpyxl

## Local Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

After startup, open the local URL printed by Streamlit in your browser.

## `.env` Configuration

Copy `.env.example` to `.env` and fill in the values as needed:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

If `.env` does not contain an API key, you can temporarily enter one in the Streamlit sidebar. The temporary key is stored only in the current session and is never written to a local file. The sidebar also provides a "Clear current API Key" button.

## DeepSeek API Key

When an API key is available, disable mock mode to call DeepSeek's OpenAI-compatible Chat Completions API. The model is instructed to return strict JSON, and the app parses the `localized_text`, `rationale`, `cultural_adaptation`, `tone_notes`, and `risk_notes` fields.

If the API is unavailable, the app falls back to mock sample results so the full workflow can still be demonstrated.

## Mock Mode

Mock mode does not require an API key. It returns sample localization results and QA notes, making it suitable for classroom demos, portfolio walkthroughs, and offline reviews.

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
- Modular engineering structure: UI, model calls, prompts, QA, terminology, and export logic are separated.
- Basic error handling: API errors, CSV format issues, and JSON parsing failures do not crash the whole page.
- Practical product judgment: different copy types map to different QA focus areas.

## Future Extensions

- Add more target languages and regional variants, such as `en-US`, `en-GB`, and `fr-CA`.
- Support fuzzy terminology matching, case checks, brand-name protection, and multi-translation management.
- Add batch retry, caching, cost tracking, and call logs.
- Introduce more detailed UI length estimation based on font, font size, and component type.
- Support human review status, reviewer notes, and second-pass rewriting.
- Add pytest unit tests and CI checks.
