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


if __name__ == '__main__':
    unittest.main()
