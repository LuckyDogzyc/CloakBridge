# CloakBridge Design

Date: 2026-05-21
Status: Draft for review
Working name: CloakBridge
Chinese name: 密桥

## Purpose

CloakBridge is a local privacy gateway for office documents. It lets users send work to powerful external AI models without sending original sensitive content outside the local machine.

The app creates sanitized versions of files, sends only sanitized content to external models, restores model responses locally, and keeps the original sensitive files, dictionaries, mappings, audit data, and logs on the user's device.

## Non-Negotiable Principles

- Original sensitive content must not be sent to external networks.
- Local sensitive dictionaries and token mappings must not be committed to GitHub or uploaded to any external service.
- The app must support macOS and Windows, with Linux support as a first-class goal.
- The first version focuses on `.docx`, `.xlsx`, and `.txt`.
- PDF, PPT, CAD, drawings, and images are outside the first version.
- Chinese language handling is a core requirement.
- Local AI must stay lightweight. Qwen 8B and expert mode are out of scope.
- Users must be able to review, add, remove, and override sensitive entities before external AI processing.
- Word and Excel formatting should be preserved when generating sanitized and restored files.

## Product Shape

CloakBridge will be a local WebUI application:

```text
Browser WebUI
  -> localhost API
Local backend service
  -> file engine, detection engine, dictionary engine, vault, model gateway
```

The local backend listens on `127.0.0.1` by default. It should not expose files or APIs to the LAN unless the user explicitly enables that later.

The app can be distributed as:

- Native installer bundles for macOS and Windows.
- Linux package or AppImage.
- Docker image for advanced users.

The UI style should later take inspiration from the Codex App: quiet, professional, sidebar-driven, review-focused, and dense enough for real work.

## First Version Scope

Supported input files:

- `.docx`
- `.xlsx`
- `.txt`

Supported workflow:

1. User uploads or selects local files.
2. App extracts text and document locations locally.
3. Rule and dictionary layer detects known sensitive content.
4. Lightweight local Chinese AI suggests additional sensitive entities.
5. User reviews detected entities.
6. User confirms, removes, edits, or adds entities.
7. Confirmed entities can be saved into project or global dictionaries.
8. App generates sanitized file or prompt content.
9. User selects an external AI provider/model.
10. App runs an outbound leakage guard before sending.
11. External AI receives only sanitized content.
12. App receives sanitized answer and optional sanitized attachments.
13. App restores sensitive terms locally.
14. WebUI shows restored answer by default and hides sanitized answer in a review/details view.

## Sensitive Entity Categories

The first version should support these categories:

- Person name
- Company or organization name
- Department name
- Project name
- Project code
- IP address
- Internal host name
- Domain
- URL
- Email address
- Mobile phone number
- Landline number
- National ID number
- Bank card number
- Unified social credit code
- Contract number
- Drawing number
- Device number
- Server number
- Custom sensitive term

Dates, money amounts, and generic locations should be configurable because some teams may need them while others may not.

## Detection Architecture

Detection runs in layers from fastest and most deterministic to more interpretive:

```text
Normalization
  -> regex rules
  -> dictionary matcher
  -> lightweight Chinese NER / classifier
  -> user review
```

### Rule Layer

The rule layer handles structured entities:

- IP addresses and CIDR ranges
- Emails
- Phone numbers
- URLs and domains
- Common ID numbers
- Contract-like identifiers
- Device/server/code patterns

Rules should be configurable per project.

### Dictionary Layer

Dictionaries are the primary long-term intelligence of the system.

Dictionary scopes:

- Global dictionary
- Project dictionary
- Session dictionary

Dictionary entry fields:

- Original text
- Entity type
- Replacement token family
- Scope
- Source: rule, local AI, user, import
- Confidence
- Status: confirmed, pending, ignored
- Created and updated timestamps

The matcher should use an Aho-Corasick style multi-pattern index in memory, backed by SQLite on disk. The app should load only the global dictionary plus the active project dictionaries for the current job. Dictionary changes should rebuild or refresh the relevant matcher without forcing a full app restart.

### Lightweight Local AI

The local AI layer should focus on Chinese-sensitive entity judgment, not content generation.

Acceptable first-version options:

- ONNX Runtime model for Chinese or multilingual NER.
- GLiNER-style local entity model if Chinese quality is acceptable.
- A small local classifier for "should this term be protected?"

Qwen 8B is explicitly out of scope. The system may later support optional local LLM providers, but the first version must not depend on them.

### Reflection Optimization

When local resources allow, the app may provide a manual "optimization review" job. This job analyzes past review decisions and suggests:

- New dictionary entries.
- New project-specific rules.
- Frequent false positives.
- Entity type corrections.
- Duplicate mappings for the same entity.

The app must not automatically apply these suggestions. Users must confirm them before they affect future processing.

## Tokenization and Restoration

Token format should be readable and stable:

```text
<PERSON_001>
<PROJECT_001>
<IP_001>
<COMPANY_001>
```

Properties:

- Same original term should map to the same token inside a project when appropriate.
- Different entity types should use different token families.
- Mappings must be stored in an encrypted local vault.
- Restoration must happen locally.
- The WebUI must default to showing restored content, not sanitized content.

For external AI responses:

- If the response is plain text, the WebUI shows restored text by default.
- The sanitized response is kept but hidden in a review/details panel.
- If the response includes an attachment, the app keeps both sanitized and restored versions for first-version inspection.
- The restored attachment should use the natural default output name and must not add terms like `converted`.

Example:

```text
Original file: 合同审查.docx
Sanitized outbound file: 合同审查.sanitized.docx
Sanitized AI attachment: 合同审查_AI回复.sanitized.docx
Restored AI attachment: 合同审查_AI回复.docx
```

## File Format Preservation

### DOCX

The app must not convert `.docx` to plain text and rebuild it from scratch. It should operate on the existing OOXML structure.

Requirements:

- Preserve paragraph styles.
- Preserve fonts, colors, bold, italic, underline, and size where possible.
- Preserve tables.
- Preserve headers and footers.
- Preserve hyperlinks and comments when feasible.
- Replace sensitive text at run or XML text-node level.
- Handle terms that cross run boundaries.
- When writing restored AI-generated content back into a `.docx`, use the surrounding paragraph or run style as the default style.

### XLSX

The app should edit the workbook without rebuilding it.

Requirements:

- Preserve sheets.
- Preserve cell styles, fonts, colors, borders, fills, widths, heights, freeze panes, merged cells, and filters where possible.
- Replace only cell string content unless explicitly configured otherwise.
- Scan sheet names, cell text, comments/notes, hyperlink display text, and workbook metadata.
- Formula values should not be modified by default. Formula strings may be scanned for sensitive literals and flagged for review.

### TXT

Requirements:

- Preserve encoding when detectable.
- Preserve line endings.
- Generate sanitized and restored text outputs.

## External Model Gateway

The model gateway should support:

- OpenAI
- Anthropic Claude
- Google Gemini
- DeepSeek
- Qwen / Tongyi
- GLM / Zhipu
- MiniMax
- OpenRouter
- Custom OpenAI-compatible endpoint
- Custom Anthropic-compatible endpoint

Provider adapters should be isolated behind one internal interface.

Before any outbound request, the gateway must run a leakage guard:

1. Check request text against the active sensitive dictionary.
2. Check request text against active mappings.
3. Check request text with high-priority regex rules such as IP, phone, email, URL, and project code patterns.
4. Block the request if raw sensitive content is detected.
5. Show the user where the leak was detected and return to review.

## Storage and Security

Local storage:

- SQLite for metadata, dictionaries, jobs, and audit records.
- Encrypted vault for mappings and sensitive dictionary data.
- Local file storage for original, sanitized, and restored files.

Security defaults:

- Bind backend to `127.0.0.1`.
- No telemetry by default.
- No external logging of prompts or original text.
- API keys stored locally and encrypted where platform support exists.
- Clear separation between source repository and user data directories.

GitHub public repository must ignore:

- Local data directories
- Vault files
- Uploads
- Outputs
- `.docx`
- `.xlsx`
- SQLite databases
- Mapping exports
- `.env` files
- API keys

The repository should include only synthetic sample data.

## Suggested Technology Stack

Frontend:

- React
- TypeScript
- Vite
- Tailwind CSS or equivalent utility styling
- Component system inspired by Codex App patterns

Backend:

- Python FastAPI
- Uvicorn local server

Document processing:

- `lxml` and direct OOXML handling for `.docx`
- `openpyxl` for `.xlsx`
- Encoding detection for `.txt`

Detection:

- Regex engine
- Aho-Corasick dictionary matcher
- Lightweight local Chinese NER/classifier

Storage:

- SQLite
- Encrypted local vault

Model gateway:

- Provider adapters
- Optional LiteLLM compatibility or reference implementation

## Testing Strategy

Tests must use synthetic documents only.

Required coverage:

- Rule detection for IP, URL, email, phone, project code, and contract-like IDs.
- Dictionary matching with large dictionaries.
- Token mapping and restoration.
- Leakage guard blocking raw sensitive content.
- `.docx` style preservation after sanitization and restoration.
- `.xlsx` style preservation after sanitization and restoration.
- WebUI review flow for confirming, ignoring, and adding sensitive terms.
- Provider adapter request construction without original sensitive text.

Performance tests:

- Large dictionary matching.
- Large `.docx` file.
- Large `.xlsx` workbook.
- Batch processing multiple files.

## Open Decisions

These decisions can wait until implementation planning:

- Exact lightweight Chinese NER model.
- Exact encryption mechanism for the vault on each platform.
- Whether LiteLLM is embedded, optional, or only used as an API-compatible reference.
- Exact packaging strategy for macOS, Windows, and Linux.
- Detailed UI layout.

## Out of Scope for First Version

- PDF processing
- PPT processing
- CAD or drawing processing
- Image OCR
- Qwen 8B or other heavy local LLM dependency
- Cloud-hosted Web App
- Automatic application of optimization suggestions
- LAN or team server mode
