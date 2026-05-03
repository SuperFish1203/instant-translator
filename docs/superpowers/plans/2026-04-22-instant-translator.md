# Instant Translator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows tray-resident instant translator that captures selected text with `Alt+T`, sends it to a configurable provider, and shows translated text in a popup near the cursor.

**Architecture:** Use a Tauri v2 shell with a Rust backend handling Windows integration and translation orchestration, and a Vue 3 frontend for the settings window and translation popup. Keep provider-specific HTTP logic behind a common Rust trait so the UI stays provider-agnostic and the popup flow only consumes normalized translation results.

**Tech Stack:** Tauri v2, Rust, Vue 3, TypeScript, Vite, Serde, Reqwest, Tokio, Tao/Tauri window APIs, Windows-specific clipboard and input crates, Vitest only if frontend helper logic becomes non-trivial

---

**Execution note:** This workspace already contains an unfinished Python skeleton in the repository root. Preserve it and build the Tauri implementation under `tauri-app/` to avoid overwriting unrelated work.

### Task 1: Bootstrap The Tauri Workspace

**Files:**
- Create: `tauri-app/package.json`
- Create: `tauri-app/src-tauri/Cargo.toml`
- Create: `tauri-app/src-tauri/tauri.conf.json`
- Create: `tauri-app/src/main.ts`
- Create: `tauri-app/src/App.vue`
- Create: `tauri-app/src-tauri/src/main.rs`

- [ ] **Step 1: Verify the current workspace is empty enough for greenfield setup**

Run: `Get-ChildItem -Force`
Expected: existing Python files remain untouched and no `tauri-app/` directory exists yet

- [ ] **Step 2: Install Rust toolchain because the machine lacks `cargo`**

Run:

```powershell
Invoke-WebRequest -Uri https://win.rustup.rs/x86_64 -OutFile rustup-init.exe
.\rustup-init.exe -y --default-toolchain stable
$env:Path += ';' + "$env:USERPROFILE\.cargo\bin"
cargo --version
```

Expected: `cargo` prints a stable toolchain version

- [ ] **Step 3: Create the Vite + Vue + TypeScript frontend shell**

Run:

```powershell
npm.cmd create vite@latest tauri-app -- --template vue-ts
```

Expected: `tauri-app/package.json`, `tauri-app/src/`, and `tauri-app/vite.config.ts` exist

- [ ] **Step 4: Add Tauri dependencies and initialize the desktop shell**

Run:

```powershell
npm.cmd install
npm.cmd install @tauri-apps/api
npm.cmd install -D @tauri-apps/cli
npm.cmd tauri init --ci --app-name InstantTranslator --window-title InstantTranslator --frontend-dist ../dist --before-dev-command "npm.cmd run dev" --before-build-command "npm.cmd run build"
```

Run in: `tauri-app`
Expected: `tauri-app/src-tauri/` and `tauri-app/src-tauri/tauri.conf.json` exist

- [ ] **Step 5: Smoke test the generated shell before feature work**

Run:

```powershell
npm.cmd tauri dev
```

Expected: the default Tauri window launches without Rust compilation errors

- [ ] **Step 6: Commit scaffold checkpoint if Git becomes available**

```bash
git add tauri-app/package.json tauri-app/package-lock.json tauri-app/src tauri-app/src-tauri
git commit -m "chore: scaffold tauri instant translator"
```

### Task 2: Add Config Persistence And Validation

**Files:**
- Create: `tauri-app/src-tauri/src/config.rs`
- Create: `tauri-app/src-tauri/src/app_state.rs`
- Modify: `tauri-app/src-tauri/src/main.rs`
- Create: `tauri-app/src/lib/config.ts`
- Create: `tauri-app/src/components/SettingsForm.vue`
- Create: `tauri-app/src/views/SettingsView.vue`
- Create: `tauri-app/src/App.vue`
- Test: `tauri-app/src-tauri/src/config.rs`

- [ ] **Step 1: Write the failing Rust tests for default config and validation**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_config_uses_alt_t_and_auto_source() {
        let config = AppConfig::default();
        assert_eq!(config.general.global_shortcut, "Alt+T");
        assert_eq!(config.language.source_mode, SourceLanguageMode::Auto);
        assert_eq!(config.language.target_language, "zh-CN");
    }

    #[test]
    fn validation_requires_provider_credentials() {
        let config = AppConfig::default();
        let error = config.validate().unwrap_err();
        assert!(error.contains("api") || error.contains("provider"));
    }
}
```

- [ ] **Step 2: Run the config tests to verify they fail**

Run: `cargo test config::tests -- --nocapture`
Expected: FAIL because `AppConfig`, `SourceLanguageMode`, and `validate` do not exist yet

- [ ] **Step 3: Implement the config model and validation**

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub general: GeneralConfig,
    pub language: LanguageConfig,
    pub provider: ProviderConfig,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            general: GeneralConfig {
                launch_on_startup: false,
                minimize_to_tray_on_close: true,
                global_shortcut: "Alt+T".into(),
                max_text_length: 5000,
                popup_width: 420.0,
            },
            language: LanguageConfig {
                source_mode: SourceLanguageMode::Auto,
                source_language: "auto".into(),
                target_language: "zh-CN".into(),
                preserve_line_breaks: true,
            },
            provider: ProviderConfig::default(),
        }
    }
}

impl AppConfig {
    pub fn validate(&self) -> Result<(), String> {
        if self.general.global_shortcut.trim().is_empty() {
            return Err("global shortcut is required".into());
        }
        if self.language.target_language.trim().is_empty() {
            return Err("target language is required".into());
        }
        self.provider.validate()
    }
}
```

- [ ] **Step 4: Run the config tests again**

Run: `cargo test config::tests -- --nocapture`
Expected: PASS

- [ ] **Step 5: Add config load/save commands in `main.rs`**

```rust
#[tauri::command]
async fn load_config(state: tauri::State<'_, AppState>) -> Result<AppConfig, String> {
    state.config_store.load().await
}

#[tauri::command]
async fn save_config(state: tauri::State<'_, AppState>, config: AppConfig) -> Result<(), String> {
    config.validate()?;
    state.config_store.save(config).await
}
```

- [ ] **Step 6: Build the settings page bound to backend commands**

```ts
export async function loadConfig(): Promise<AppConfig> {
  return invoke<AppConfig>("load_config");
}

export async function saveConfig(config: AppConfig): Promise<void> {
  await invoke("save_config", { config });
}
```

- [ ] **Step 7: Run the shell to verify settings can load and save**

Run: `npm.cmd tauri dev`
Expected: settings window opens and can persist config without runtime errors

- [ ] **Step 8: Commit the config milestone if Git is available**

```bash
git add tauri-app/src-tauri/src/config.rs tauri-app/src-tauri/src/app_state.rs tauri-app/src-tauri/src/main.rs tauri-app/src/lib/config.ts tauri-app/src/components/SettingsForm.vue tauri-app/src/views/SettingsView.vue tauri-app/src/App.vue
git commit -m "feat: add translator configuration flow"
```

### Task 3: Implement Provider Abstraction And OpenAI-Compatible Translation

**Files:**
- Create: `tauri-app/src-tauri/src/providers/mod.rs`
- Create: `tauri-app/src-tauri/src/providers/openai_compatible.rs`
- Modify: `tauri-app/src-tauri/src/config.rs`
- Modify: `tauri-app/src-tauri/src/app_state.rs`
- Modify: `tauri-app/src-tauri/src/main.rs`
- Test: `tauri-app/src-tauri/src/providers/openai_compatible.rs`

- [ ] **Step 1: Write the failing tests for prompt construction and response parsing**

```rust
#[tokio::test]
async fn builds_openai_request_with_target_language_only_output() {
    let provider = OpenAiCompatibleProvider::new(OpenAiCompatibleConfig {
        base_url: "http://localhost:1234/v1".into(),
        api_key: "test".into(),
        model: "local-model".into(),
        headers: vec![],
        system_prompt_template: "Translate into {target_language}. Output translated text only.".into(),
    });

    let body = provider.build_request_body(&TranslateRequest {
        text: "hello".into(),
        source_language: None,
        target_language: "zh-CN".into(),
    });

    assert!(body.to_string().contains("translated text only"));
    assert!(body.to_string().contains("zh-CN"));
}

#[test]
fn parses_openai_response_text() {
    let json = serde_json::json!({
        "choices": [
            { "message": { "content": "你好" } }
        ]
    });
    let translated = extract_openai_translation(&json).unwrap();
    assert_eq!(translated, "你好");
}
```

- [ ] **Step 2: Run the provider tests to verify they fail**

Run: `cargo test openai_compatible -- --nocapture`
Expected: FAIL because the provider types do not exist yet

- [ ] **Step 3: Implement the provider trait and OpenAI-compatible adapter**

```rust
#[async_trait::async_trait]
pub trait TranslationProvider: Send + Sync {
    async fn translate(&self, request: TranslateRequest) -> Result<TranslateResponse, ProviderError>;
}

pub struct OpenAiCompatibleProvider {
    client: reqwest::Client,
    config: OpenAiCompatibleConfig,
}

#[async_trait::async_trait]
impl TranslationProvider for OpenAiCompatibleProvider {
    async fn translate(&self, request: TranslateRequest) -> Result<TranslateResponse, ProviderError> {
        let payload = self.build_request_body(&request);
        let response = self.client
            .post(format!("{}/chat/completions", self.config.base_url.trim_end_matches('/')))
            .bearer_auth(&self.config.api_key)
            .json(&payload)
            .send()
            .await?;
        let json: serde_json::Value = response.json().await?;
        let translated_text = extract_openai_translation(&json)?;
        Ok(TranslateResponse {
            translated_text,
            detected_source_language: request.source_language,
            provider_name: "openai-compatible".into(),
        })
    }
}
```

- [ ] **Step 4: Run the OpenAI provider tests again**

Run: `cargo test openai_compatible -- --nocapture`
Expected: PASS

- [ ] **Step 5: Add a backend translation command that dispatches through the provider**

```rust
#[tauri::command]
async fn translate_text(
    state: tauri::State<'_, AppState>,
    text: String,
) -> Result<TranslateResponse, String> {
    state.translator.translate_selected_text(text).await
}
```

- [ ] **Step 6: Verify the backend still builds**

Run: `cargo test`
Expected: PASS with provider tests included

- [ ] **Step 7: Commit the OpenAI-compatible milestone if Git is available**

```bash
git add tauri-app/src-tauri/src/providers/mod.rs tauri-app/src-tauri/src/providers/openai_compatible.rs tauri-app/src-tauri/src/config.rs tauri-app/src-tauri/src/app_state.rs tauri-app/src-tauri/src/main.rs
git commit -m "feat: add openai compatible translation provider"
```

### Task 4: Add Google And Tencent Providers

**Files:**
- Create: `tauri-app/src-tauri/src/providers/google_translate.rs`
- Create: `tauri-app/src-tauri/src/providers/tencent_translate.rs`
- Modify: `tauri-app/src-tauri/src/providers/mod.rs`
- Modify: `tauri-app/src-tauri/src/config.rs`
- Test: `tauri-app/src-tauri/src/providers/google_translate.rs`
- Test: `tauri-app/src-tauri/src/providers/tencent_translate.rs`

- [ ] **Step 1: Write failing parser and validation tests for Google and Tencent providers**

```rust
#[test]
fn parses_google_translation_response() {
    let json = serde_json::json!({
        "data": {
            "translations": [
                { "translatedText": "你好", "detectedSourceLanguage": "en" }
            ]
        }
    });
    let response = parse_google_translation(&json).unwrap();
    assert_eq!(response.translated_text, "你好");
    assert_eq!(response.detected_source_language.as_deref(), Some("en"));
}

#[test]
fn tencent_validation_requires_secret_pair() {
    let config = TencentTranslateConfig::default();
    let error = config.validate().unwrap_err();
    assert!(error.contains("SecretId"));
}
```

- [ ] **Step 2: Run those tests to verify they fail**

Run:

```powershell
cargo test parses_google_translation_response -- --nocapture
cargo test tencent_validation_requires_secret_pair -- --nocapture
```

Expected: FAIL because parsing and validation functions do not exist yet

- [ ] **Step 3: Implement the Google provider**

```rust
pub struct GoogleTranslateProvider {
    client: reqwest::Client,
    config: GoogleTranslateConfig,
}

#[async_trait::async_trait]
impl TranslationProvider for GoogleTranslateProvider {
    async fn translate(&self, request: TranslateRequest) -> Result<TranslateResponse, ProviderError> {
        let response = self.client
            .post("https://translation.googleapis.com/language/translate/v2")
            .query(&[("key", self.config.api_key.as_str())])
            .json(&build_google_payload(&request))
            .send()
            .await?;
        parse_google_translation_response(response).await
    }
}
```

- [ ] **Step 4: Implement the Tencent provider**

```rust
pub struct TencentTranslateProvider {
    client: reqwest::Client,
    config: TencentTranslateConfig,
}

#[async_trait::async_trait]
impl TranslationProvider for TencentTranslateProvider {
    async fn translate(&self, request: TranslateRequest) -> Result<TranslateResponse, ProviderError> {
        let signed_request = build_tencent_request(&self.config, &request)?;
        let response = self.client
            .post("https://tmt.tencentcloudapi.com")
            .headers(signed_request.headers)
            .body(signed_request.body)
            .send()
            .await?;
        parse_tencent_translation_response(response).await
    }
}
```

- [ ] **Step 5: Run the full provider suite**

Run: `cargo test providers -- --nocapture`
Expected: PASS

- [ ] **Step 6: Confirm settings validation switches by selected provider**

Run: `cargo test config::tests -- --nocapture`
Expected: PASS with provider-specific credential rules enforced

- [ ] **Step 7: Commit the multi-provider milestone if Git is available**

```bash
git add tauri-app/src-tauri/src/providers/google_translate.rs tauri-app/src-tauri/src/providers/tencent_translate.rs tauri-app/src-tauri/src/providers/mod.rs tauri-app/src-tauri/src/config.rs
git commit -m "feat: add google and tencent translation providers"
```

### Task 5: Build The Popup Window And Frontend Translation States

**Files:**
- Create: `tauri-app/src/components/TranslatePopup.vue`
- Create: `tauri-app/src/lib/translation.ts`
- Modify: `tauri-app/src/App.vue`
- Modify: `tauri-app/src-tauri/tauri.conf.json`
- Test: `tauri-app/src/lib/translation.test.ts`

- [ ] **Step 1: Write the failing frontend helper test for popup state reduction**

```ts
import { describe, expect, it } from "vitest";
import { reduceTranslationState } from "./translation";

describe("reduceTranslationState", () => {
  it("keeps only the latest translation request", () => {
    const state = reduceTranslationState(
      { activeRequestId: 1, status: "loading", text: "" },
      { type: "translate-success", requestId: 2, text: "你好" },
    );

    expect(state.activeRequestId).toBe(2);
    expect(state.status).toBe("success");
    expect(state.text).toBe("你好");
  });
});
```

- [ ] **Step 2: Run the frontend test to verify it fails**

Run: `npm.cmd exec vitest run src/lib/translation.test.ts`
Expected: FAIL because the helper and test runner are not wired yet

- [ ] **Step 3: Add Vitest and implement the helper**

```powershell
npm.cmd install -D vitest
```

```ts
export function reduceTranslationState(state: PopupState, event: PopupEvent): PopupState {
  if (event.requestId < state.activeRequestId) {
    return state;
  }

  switch (event.type) {
    case "translate-loading":
      return { activeRequestId: event.requestId, status: "loading", text: "" };
    case "translate-success":
      return { activeRequestId: event.requestId, status: "success", text: event.text };
    case "translate-error":
      return { activeRequestId: event.requestId, status: "error", text: event.message };
  }
}
```

- [ ] **Step 4: Run the frontend helper test again**

Run: `npm.cmd exec vitest run src/lib/translation.test.ts`
Expected: PASS

- [ ] **Step 5: Implement the popup component**

```vue
<template>
  <main class="popup-shell" :class="status">
    <p v-if="status === 'loading'">Translating...</p>
    <p v-else class="translated-text">{{ text }}</p>
  </main>
</template>
```

- [ ] **Step 6: Configure the popup as a dedicated Tauri window**

```json
{
  "app": {
    "windows": [
      { "label": "settings", "title": "InstantTranslator", "resizable": true },
      { "label": "popup", "title": "Translation", "decorations": false, "alwaysOnTop": true, "visible": false, "resizable": true }
    ]
  }
}
```

- [ ] **Step 7: Verify the app starts with the popup window hidden and the settings window visible**

Run: `npm.cmd tauri dev`
Expected: the app launches and only the main settings window is shown initially

- [ ] **Step 8: Commit the popup UI milestone if Git is available**

```bash
git add tauri-app/src/components/TranslatePopup.vue tauri-app/src/lib/translation.ts tauri-app/src/lib/translation.test.ts tauri-app/src/App.vue tauri-app/src-tauri/tauri.conf.json tauri-app/package.json tauri-app/package-lock.json
git commit -m "feat: add translation popup ui"
```

### Task 6: Implement Tray, Global Shortcut, Clipboard Capture, And Translation Orchestration

**Files:**
- Create: `tauri-app/src-tauri/src/hotkey.rs`
- Create: `tauri-app/src-tauri/src/clipboard.rs`
- Create: `tauri-app/src-tauri/src/windowing.rs`
- Create: `tauri-app/src-tauri/src/translator.rs`
- Modify: `tauri-app/src-tauri/src/main.rs`
- Modify: `tauri-app/src-tauri/src/app_state.rs`
- Test: `tauri-app/src-tauri/src/windowing.rs`
- Test: `tauri-app/src-tauri/src/translator.rs`

- [ ] **Step 1: Write the failing Rust tests for popup positioning and overlength rejection**

```rust
#[test]
fn popup_position_is_clamped_inside_monitor() {
    let position = clamp_popup_position(
        (1910.0, 1070.0),
        (420.0, 280.0),
        (0.0, 0.0, 1920.0, 1080.0),
    );

    assert!(position.0 <= 1500.0);
    assert!(position.1 <= 800.0);
}

#[test]
fn translator_rejects_text_over_limit() {
    let mut config = AppConfig::default();
    config.general.max_text_length = 5;
    let error = Translator::new(config, ProviderDispatcher::failing_stub())
        .validate_text("toolong")
        .unwrap_err();
    assert!(error.contains("length"));
}
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run:

```powershell
cargo test popup_position_is_clamped_inside_monitor -- --nocapture
cargo test translator_rejects_text_over_limit -- --nocapture
```

Expected: FAIL because positioning and translator logic do not exist yet

- [ ] **Step 3: Implement popup positioning and translator validation**

```rust
pub fn clamp_popup_position(
    cursor: (f64, f64),
    popup: (f64, f64),
    monitor: (f64, f64, f64, f64),
) -> (f64, f64) {
    let mut x = cursor.0 + 16.0;
    let mut y = cursor.1 + 16.0;
    let max_x = monitor.0 + monitor.2 - popup.0;
    let max_y = monitor.1 + monitor.3 - popup.1;
    x = x.clamp(monitor.0, max_x);
    y = y.clamp(monitor.1, max_y);
    (x, y)
}

impl Translator {
    pub fn validate_text(&self, text: &str) -> Result<(), String> {
        if text.trim().is_empty() {
            return Err("no text captured".into());
        }
        if text.chars().count() > self.config.general.max_text_length as usize {
            return Err("text length exceeds configured maximum".into());
        }
        Ok(())
    }
}
```

- [ ] **Step 4: Run the tests again**

Run:

```powershell
cargo test popup_position_is_clamped_inside_monitor -- --nocapture
cargo test translator_rejects_text_over_limit -- --nocapture
```

Expected: PASS

- [ ] **Step 5: Implement clipboard capture and restore**

```rust
pub async fn capture_selected_text() -> Result<String, ClipboardError> {
    let snapshot = ClipboardSnapshot::capture_all()?;
    send_ctrl_c()?;
    let captured = wait_for_clipboard_text(Duration::from_millis(350))?;
    snapshot.restore()?;
    Ok(captured)
}
```

- [ ] **Step 6: Register the tray and global shortcut, then wire translation events to the popup**

```rust
app.handle().plugin(tauri_plugin_global_shortcut::Builder::new().build())?;
tauri_plugin_global_shortcut::register(app.handle(), "Alt+T", move || {
    let handle = app_handle.clone();
    tauri::async_runtime::spawn(async move {
        run_translation_flow(handle).await;
    });
})?;
```

- [ ] **Step 7: Run the application manually and verify the end-to-end flow**

Run: `npm.cmd tauri dev`
Expected: the app stays in the tray, `Alt+T` triggers translation, and the popup appears near the cursor

- [ ] **Step 8: Commit the desktop orchestration milestone if Git is available**

```bash
git add tauri-app/src-tauri/src/hotkey.rs tauri-app/src-tauri/src/clipboard.rs tauri-app/src-tauri/src/windowing.rs tauri-app/src-tauri/src/translator.rs tauri-app/src-tauri/src/main.rs tauri-app/src-tauri/src/app_state.rs
git commit -m "feat: wire shortcut clipboard and popup translation flow"
```

### Task 7: Add Logging, Packaging Checks, And Release Verification

**Files:**
- Create: `tauri-app/src-tauri/src/logging.rs`
- Modify: `tauri-app/src-tauri/src/main.rs`
- Modify: `tauri-app/src-tauri/Cargo.toml`
- Modify: `tauri-app/src-tauri/tauri.conf.json`
- Create: `tauri-app/README.md`

- [ ] **Step 1: Write the failing Rust test for log path resolution**

```rust
#[test]
fn resolves_log_file_inside_app_data_directory() {
    let path = resolve_log_path("InstantTranslator").unwrap();
    assert!(path.ends_with("InstantTranslator\\logs\\app.log"));
}
```

- [ ] **Step 2: Run the logging test to verify it fails**

Run: `cargo test logging -- --nocapture`
Expected: FAIL because the logging module does not exist yet

- [ ] **Step 3: Implement logging setup**

```rust
pub fn init_logging(app_name: &str) -> Result<(), String> {
    let path = resolve_log_path(app_name)?;
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|err| err.to_string())?;
    }
    tracing_appender::rolling::never(
        path.parent().unwrap(),
        path.file_name().unwrap().to_string_lossy().as_ref(),
    );
    Ok(())
}
```

- [ ] **Step 4: Run the logging test again**

Run: `cargo test logging -- --nocapture`
Expected: PASS

- [ ] **Step 5: Build the release executable**

Run: `npm.cmd tauri build`
Expected: PASS and a Windows `.exe` is produced under the Tauri bundle output

- [ ] **Step 6: Document operator setup for provider configuration**

```md
# InstantTranslator

1. Launch the packaged `.exe`
2. Open settings from the tray icon
3. Choose a provider
4. Enter provider credentials and language options
5. Select text anywhere in Windows and press `Alt+T`
```

- [ ] **Step 7: Perform final manual verification**

Run: `npm.cmd tauri dev`
Expected:
- settings persist
- tray behavior works
- clipboard is restored
- popup resizes horizontally
- each configured provider path reports understandable errors when misconfigured

- [ ] **Step 8: Commit the release-prep milestone if Git is available**

```bash
git add tauri-app/src-tauri/src/logging.rs tauri-app/src-tauri/src/main.rs tauri-app/src-tauri/Cargo.toml tauri-app/src-tauri/tauri.conf.json tauri-app/README.md
git commit -m "chore: finalize logging packaging and docs"
```
