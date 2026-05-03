# Windows Instant Translator Design

## Summary

Build a Windows desktop translator that runs in the background, stays in the system tray, listens for the global shortcut `Alt+T`, captures the currently selected text by simulating `Ctrl+C`, sends the text to a configurable translation provider, and shows the translated result in a lightweight popup near the mouse cursor.

The first release is intentionally narrow:

- Windows only
- Background resident app with tray icon
- Global `Alt+T` shortcut
- Clipboard backup and restore around simulated copy
- Configurable source language strategy and target language
- Multiple providers: OpenAI-compatible API, Google Translate API, Tencent Cloud Translate API
- Popup shows translated text only
- Popup can be resized horizontally by dragging its edge
- Packaged as a standalone `.exe` for end users

## User-Confirmed Product Decisions

- Target language behavior: configured in settings and used by the shortcut flow
- Provider support: OpenAI-compatible API plus mainstream translation providers such as Google Translate API and Tencent Cloud Translate API
- Selection capture strategy: simulate copy, restore clipboard afterward
- Popup behavior: stay visible until closed or focus is lost
- Close behavior: closing the main window minimizes to tray and keeps the app running
- Distribution: standalone Windows `.exe`, no Python/Node environment required for end users
- Popup content: translated text only
- Popup layout: horizontally resizable by dragging the window edge
- Source language strategy: default auto-detect, with optional manual override in settings
- Popup position: appear near the mouse cursor by default

## Non-Goals For V1

- OCR or screenshot translation
- Translation history
- Multiple shortcut profiles
- Secure OS credential vault integration
- Provider plugin marketplace
- Cross-platform support

## Technical Direction

Use `Tauri v2 + Rust + Vue 3 + TypeScript`.

Reasoning:

- Tauri keeps the packaged application smaller than Electron
- Rust is the best place for Windows-specific integration such as tray behavior, keyboard hooks, clipboard handling, and popup positioning
- The frontend only needs lightweight UI for settings and popup rendering
- Provider integration can live behind a Rust abstraction so the UI stays provider-agnostic

## Current Environment Constraints

The current workspace appears to be empty and suitable for a greenfield build.

The local machine currently has:

- `node.exe`
- `npm.cmd`
- `python`

The local machine currently does not have:

- `git`
- `rustc`
- `cargo`
- `rustup`
- `winget`

This does not change the application design, but it affects the implementation plan. The plan must include explicit bootstrap steps for the Rust and Tauri toolchain before feature development starts.

## Architecture

The application is split into four units with clear responsibilities.

### 1. Rust Background Core

Responsibilities:

- Initialize the Tauri application
- Register and listen for the global shortcut `Alt+T`
- Handle system tray setup and tray menu actions
- Simulate `Ctrl+C` to capture selected text
- Backup and restore clipboard contents
- Call the translation provider layer
- Position and show or hide the popup window
- Persist and load local configuration
- Centralize error handling and logging

### 2. Tauri Window Layer

Two windows are required.

`SettingsWindow`

- Normal app window for configuring behavior and provider settings
- Hidden instead of exiting when the user closes it
- Re-openable from the tray menu

`TranslatePopupWindow`

- Small frameless popup
- Always on top
- Displays translated text only
- Resizable horizontally by dragging the edge
- Appears near the mouse cursor
- Hides on focus loss or explicit close
- Reuses the same window instance for repeated translations

### 3. Frontend UI Layer

Responsibilities:

- Render the settings form
- Render the translated text popup
- Display loading and error states
- Validate user input before saving settings
- Communicate with the Rust backend through Tauri commands and events

The frontend should remain thin. It must not perform OS integration directly.

### 4. Translation Provider Layer

Responsibilities:

- Define a unified translation request and response model
- Map provider-specific settings into HTTP requests
- Parse provider-specific responses into a common translation result
- Normalize provider errors into user-facing and log-friendly error forms

## Runtime Flow

### Main Translation Flow

1. The user selects text in any Windows application.
2. The user presses `Alt+T`.
3. The Rust shortcut handler starts a translation job.
4. The app captures the current clipboard contents, including available formats that can be restored safely.
5. The app simulates `Ctrl+C`.
6. The app waits briefly and polls clipboard text changes within a bounded timeout.
7. If no text is captured, the app restores the clipboard and shows a short failure state.
8. If text is captured, the app restores the original clipboard immediately.
9. The app loads the saved configuration.
10. The app resolves source language behavior:
    - If source language mode is `auto`, provider-side auto detection is used where supported.
    - If source language mode is `manual`, the configured source language code is sent.
11. The app sends the request to the selected provider.
12. The app calculates popup coordinates near the current mouse cursor and clamps them into the visible monitor bounds.
13. The popup window opens or refreshes in place.
14. The popup shows one of three states:
    - loading
    - translated text
    - error message
15. The popup hides on focus loss or explicit close.

### Repeated Shortcut Behavior

- Repeated `Alt+T` presses reuse the same popup window instance
- If a translation is already in flight, only the latest request is kept
- Earlier unfinished requests are ignored once superseded

### Clipboard Safety Rules

- The original clipboard must be restored whether translation succeeds or fails
- Translation must not leave copied text behind in the clipboard unless restoring fails
- Restore failures must be logged
- The UI should remain responsive even if clipboard capture fails

## Window Behavior

### Settings Window

- Opened from tray icon interaction or tray menu
- Closing the window hides it to tray instead of terminating the process
- Contains all user-editable configuration

### Popup Window

- Frameless and lightweight
- Shows translated text only
- Supports vertical scrolling for long results
- Supports horizontal resizing by dragging the edge
- Width is persisted as part of user settings
- Height adapts to content up to a reasonable maximum, after which scrolling is used
- Positioned near the mouse cursor
- Repositioned to stay inside the current monitor work area
- Hidden when focus is lost

## Configuration Model

Store configuration in the application data directory, for example:

`%AppData%/<app-name>/config.json`

The configuration schema for V1 should contain:

```json
{
  "general": {
    "launchOnStartup": false,
    "minimizeToTrayOnClose": true,
    "globalShortcut": "Alt+T",
    "maxTextLength": 5000,
    "popupWidth": 420
  },
  "language": {
    "sourceMode": "auto",
    "sourceLanguage": "auto",
    "targetLanguage": "zh-CN",
    "preserveLineBreaks": true
  },
  "provider": {
    "kind": "openai-compatible",
    "openaiCompatible": {
      "baseUrl": "",
      "apiKey": "",
      "model": "",
      "headers": [
        {
          "name": "",
          "value": ""
        }
      ],
      "systemPromptTemplate": "Translate the following text into {target_language}. Output translated text only."
    },
    "googleTranslate": {
      "apiKey": ""
    },
    "tencentTranslate": {
      "secretId": "",
      "secretKey": "",
      "region": "",
      "projectId": 0
    }
  }
}
```

Notes:

- `sourceLanguage` is ignored when `sourceMode` is `auto`
- `popupWidth` is updated whenever the user resizes the popup horizontally
- Sensitive fields are stored locally in plain configuration for V1 to keep implementation simple

## Provider Abstraction

The backend defines a common request:

```rust
struct TranslateRequest {
    text: String,
    source_language: Option<String>,
    target_language: String,
}
```

The backend defines a common response:

```rust
struct TranslateResponse {
    translated_text: String,
    detected_source_language: Option<String>,
    provider_name: String,
}
```

The backend defines a provider trait:

```rust
trait TranslationProvider {
    async fn translate(&self, request: TranslateRequest) -> Result<TranslateResponse, ProviderError>;
}
```

Provider-specific rules:

### OpenAI-Compatible Provider

- User provides `baseUrl`, `apiKey`, `model`, optional headers, optional prompt template
- Request is sent to a chat-completions-compatible or responses-compatible endpoint selected by implementation
- The prompt must instruct the model to return translated text only
- The response parser extracts the translated text from the provider response body

### Google Translate Provider

- User provides `apiKey`
- The backend sends text, source language when manually set, and target language
- The response parser extracts translated text and detected source language where available

### Tencent Cloud Translate Provider

- User provides `secretId`, `secretKey`, `region`, optional `projectId`
- The backend signs the request according to Tencent Cloud requirements
- The response parser extracts translated text and detected source language where available

## Error Model

User-facing error states are normalized into four categories.

### 1. No Text Captured

Displayed message:

`未检测到可翻译文本`

### 2. Missing Configuration

Displayed message:

`请先在设置中完成翻译服务配置`

### 3. Request Failure

Displayed message:

`翻译请求失败，请检查接口地址或网络连接`

### 4. Provider Response Failure

Displayed message:

`翻译服务返回异常，请检查密钥、模型或额度`

Logging rules:

- Full technical details are written to an app log file
- UI shows concise messages only
- Secrets must never be written to logs

Suggested log path:

`%AppData%/<app-name>/logs/app.log`

## Input Validation Rules

Before saving settings or sending translation requests, enforce the following:

- Global shortcut must not be empty
- Target language must be selected
- `maxTextLength` must be a positive integer
- `popupWidth` must be within a bounded range such as `280` to `900`
- Provider-specific required fields must be present for the selected provider
- OpenAI-compatible custom header rows with empty names are ignored
- If captured text length exceeds `maxTextLength`, the app must reject the request with a clear error instead of truncating silently

## Data Boundaries And Responsibilities

Recommended project structure:

- `src-tauri/src/main.rs`: Tauri entry and high-level wiring
- `src-tauri/src/app_state.rs`: shared runtime state
- `src-tauri/src/hotkey.rs`: global shortcut handling
- `src-tauri/src/clipboard.rs`: clipboard backup, capture, restore
- `src-tauri/src/windowing.rs`: popup positioning and window visibility control
- `src-tauri/src/config.rs`: config model, persistence, validation
- `src-tauri/src/logging.rs`: file logging setup
- `src-tauri/src/providers/mod.rs`: provider interface and dispatch
- `src-tauri/src/providers/openai_compatible.rs`: OpenAI-compatible implementation
- `src-tauri/src/providers/google_translate.rs`: Google implementation
- `src-tauri/src/providers/tencent_translate.rs`: Tencent implementation
- `src/components/SettingsForm.vue`: settings UI
- `src/components/TranslatePopup.vue`: popup UI
- `src/views/SettingsView.vue`: settings page composition
- `src/stores/settings.ts`: frontend settings state
- `src/lib/types.ts`: shared frontend types

## Packaging

Release packaging target:

- Windows standalone `.exe`

Distribution expectations:

- End users should not need Node.js, Rust, Python, or any manual runtime installation
- The packaged app should include all runtime dependencies required by Tauri

## Testing Strategy

### Rust Unit Tests

- Config loading and saving
- Config validation
- Provider request construction
- Provider response parsing
- Language resolution behavior
- Popup positioning calculations

### Rust Integration Tests

- Missing configuration behavior
- Provider error mapping
- Overlength text rejection
- Translation dispatch selection based on configured provider

### Manual Acceptance Coverage

- Tray icon is visible and functional
- Main window hides to tray on close
- Shortcut works in common apps such as Notepad, browser, chat apps, and IDEs
- Clipboard contents are restored after translation
- Popup appears near the cursor and stays inside monitor bounds
- Popup hides on focus loss
- Popup width resizing is persisted
- API misconfiguration produces understandable errors
- Packaged `.exe` starts and runs on a machine without development tooling

## Release Criteria For V1

V1 is complete when all of the following are true:

- A user can launch the app on Windows and keep it running in the tray
- A user can open settings and configure one supported provider successfully
- A user can choose automatic or manual source language behavior
- A user can choose a target language
- A user can select text in another application and press `Alt+T`
- The app captures the selected text reliably using simulated copy
- The app restores the previous clipboard contents after capture
- The app sends the text to the configured provider
- The popup appears near the cursor and shows translated text only
- The popup can be resized horizontally
- The app can be distributed as a standalone `.exe`

## Implementation Risks

### 1. Global Shortcut Integration

Risk:

Tauri plugin coverage for global shortcuts and Windows behavior may vary by version.

Mitigation:

Prefer a maintained Tauri-compatible shortcut solution early and test it before building provider logic.

### 2. Clipboard Round-Trip Reliability

Risk:

Some applications may delay or block copy behavior.

Mitigation:

Use bounded polling, clear failure handling, and application-level manual verification across common target apps.

### 3. Provider API Differences

Risk:

OpenAI-compatible services vary in endpoint behavior and response shapes.

Mitigation:

Design the OpenAI-compatible adapter with clear request and response normalization and validate against at least one local-model-compatible endpoint during implementation.

### 4. Toolchain Bootstrap

Risk:

The current machine lacks Rust tooling and Git.

Mitigation:

Make environment bootstrap a first-class task in the implementation plan before any feature work.
