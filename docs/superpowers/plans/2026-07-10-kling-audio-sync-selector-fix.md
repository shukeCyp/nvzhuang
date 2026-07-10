# Kling Audio Sync Selector Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Kling video generation tolerate the current `音画同步` checkbox markup and continue when the control is absent or unrecognizable.

**Architecture:** Add a pure status parser for current `svg[icon-name]` and legacy `xlink:href` values. `_set_ui_params` will use that parser after safely checking for the setting control, clicking it only when the parsed state is enabled; missing or unknown state logs a warning and leaves the rest of the generation flow unchanged.

**Tech Stack:** Python 3.12, Playwright async API, unittest.

## Global Constraints

- Keep the existing `KlingVideoGenerator` public API unchanged.
- Do not submit a Kling generation task during automated tests.
- Preserve legacy `xlink:href` support while prioritizing `svg[icon-name]`.
- Missing or unknown audio-sync state must not abort video generation.

---

### Task 1: Add a regression test for audio-sync state parsing

**Files:**
- Create: `tests/test_kling_video_generator.py`
- Modify: none
- Test: `tests/test_kling_video_generator.py`

**Interfaces:**
- Consumes: `backend/kling_video_generator.py`
- Produces: regression expectations for `_audio_sync_enabled(icon_name, legacy_href)`.

- [ ] **Step 1: Write the failing test**

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from kling_video_generator import _audio_sync_enabled


class AudioSyncStateTests(unittest.TestCase):
    def test_current_checked_icon_is_enabled(self):
        self.assertTrue(_audio_sync_enabled('IconCheckboxCheckedSecondary', None))

    def test_current_unchecked_icon_is_disabled(self):
        self.assertFalse(_audio_sync_enabled('IconCheckboxUncheckedSecondary', None))

    def test_legacy_unchecked_href_is_disabled(self):
        self.assertFalse(_audio_sync_enabled(None, '#icon-unchecked'))

    def test_missing_icon_state_is_unknown(self):
        self.assertIsNone(_audio_sync_enabled(None, None))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && python -m unittest tests.test_kling_video_generator.AudioSyncStateTests -v`

Expected: FAIL with an import error because `_audio_sync_enabled` does not yet exist.

- [ ] **Step 3: Commit the red test**

```bash
git add tests/test_kling_video_generator.py
git commit -m "test: cover Kling audio sync icon states"
```

### Task 2: Implement compatible audio-sync handling

**Files:**
- Create: none
- Modify: `backend/kling_video_generator.py:15-225`
- Test: `tests/test_kling_video_generator.py`

**Interfaces:**
- Consumes: `_audio_sync_enabled(icon_name: str | None, legacy_href: str | None) -> bool | None`
- Produces: `_set_ui_params(page, model, quality, duration)` that never waits on a missing audio-sync icon.

- [ ] **Step 1: Implement the pure parser**

Add near the module constants:

```python
def _audio_sync_enabled(icon_name: str | None, legacy_href: str | None) -> bool | None:
    icon_value = (icon_name or '').lower()
    if 'unchecked' in icon_value:
        return False
    if 'checked' in icon_value:
        return True

    href_value = (legacy_href or '').lower()
    if href_value:
        return 'unchecked' not in href_value
    return None
```

- [ ] **Step 2: Replace the fragile UI lookup**

Replace the direct `.svg-icon use` lookup in `_set_ui_params` with this bounded lookup:

```python
sync_btn = page.locator('.setting-switch', has_text='音画同步').first
if await sync_btn.count() == 0:
    log.warning('未找到音画同步开关，跳过该设置')
else:
    current_icon = sync_btn.locator('svg[icon-name]').first
    legacy_icon = sync_btn.locator('.svg-icon use').first
    icon_name = await current_icon.get_attribute('icon-name') if await current_icon.count() else None
    legacy_href = await legacy_icon.get_attribute('xlink:href') if await legacy_icon.count() else None
    sync_enabled = _audio_sync_enabled(icon_name, legacy_href)
    if sync_enabled is True:
        await sync_btn.click()
        await asyncio.sleep(0.3)
        log.info('已取消音画同步')
    elif sync_enabled is None:
        log.warning('无法识别音画同步开关状态，跳过该设置')
```

- [ ] **Step 3: Run the regression test to verify it passes**

Run: `source .venv/bin/activate && python -m unittest tests.test_kling_video_generator.AudioSyncStateTests -v`

Expected: PASS with four tests run and zero failures.

- [ ] **Step 4: Run the existing test suite**

Run: `source .venv/bin/activate && python -m unittest discover -s tests -v`

Expected: PASS with the new audio-sync tests and existing crawler tests.

- [ ] **Step 5: Commit the implementation**

```bash
git add backend/kling_video_generator.py tests/test_kling_video_generator.py
git commit -m "fix: support current Kling audio sync checkbox"
```

### Task 3: Verify the current page without submitting a task

**Files:**
- Create: none
- Modify: none
- Test: ad-hoc authenticated Playwright diagnostic

**Interfaces:**
- Consumes: `KlingVideoGenerator._set_ui_params(page, model, quality, duration)` and saved `kling_cookies`.
- Produces: evidence that the current page reaches the setting-selection phase without the former audio-sync timeout.

- [ ] **Step 1: Run the no-submit page verification**

Run the existing diagnostic flow that injects `data/settings/kling_cookies.json`, opens `https://klingai.com/app/video/new?ac=1`, writes preferences, and calls `_set_ui_params` without uploading an image or clicking the generate button.

- [ ] **Step 2: Verify the result**

Expected: output contains `UI 参数设置成功`; output does not contain `Locator.get_attribute` waiting for `.setting-switch .svg-icon use`.

- [ ] **Step 3: Commit plan and implementation history is already recorded**

```bash
git status --short
```

Expected: no unintended working-tree changes.
