import pathlib
import tempfile
import unittest

from scripts.patch_alc888_probe import patch_legacy, patch_modern


class PatchTests(unittest.TestCase):
    def test_legacy_identity(self):
        source = (
            "static int stac9220Construct(PHDACODEC pThis)\n{\n"
            "    pThis->u16VendorId  = 0x8384; /* SigmaTel */\n"
            "    pThis->u16DeviceId  = 0x7680; /* STAC9221 A1 */\n"
            "}\n"
        )
        result = patch_legacy(source)
        self.assertIn("pThis->u16VendorId  = 0x10EC;", result)
        self.assertIn("pThis->u16DeviceId  = 0x0888;", result)
        self.assertIn("VBOX_ALC888_IDENTITY_PROBE", result)

    def test_modern_identity(self):
        source = (
            "static int stac9220Construct(PHDACODECR3 pThis, HDACODECCFG *pCfg)\n{\n"
            "    pCfg->idVendor          = 0x8384; /* SigmaTel */\n"
            "    pCfg->idDevice          = 0x7680; /* STAC9221 A1 */\n"
            "}\n"
        )
        result = patch_modern(source)
        self.assertIn("pCfg->idVendor          = 0x10EC;", result)
        self.assertIn("pCfg->idDevice          = 0x0888;", result)

    def test_wrong_source_fails_closed(self):
        with self.assertRaises(RuntimeError):
            patch_legacy("int unrelated = 1;\n")

    def test_requires_exactly_one_assignment(self):
        source = (
            "pThis->u16VendorId = 0x8384;\n"
            "pThis->u16VendorId = 0x8384;\n"
            "pThis->u16DeviceId = 0x7680;\n"
        )
        with self.assertRaises(RuntimeError):
            patch_legacy(source)

    def test_patch_is_idempotent(self):
        source = (
            "pThis->u16VendorId = 0x8384;\n"
            "pThis->u16DeviceId = 0x7680;\n"
        )
        once = patch_legacy(source)
        self.assertEqual(patch_legacy(once), once)

    def test_partial_patch_is_rejected(self):
        source = (
            "pThis->u16VendorId = 0x10EC; "
            "/* VBOX_ALC888_IDENTITY_PROBE */\n"
            "pThis->u16DeviceId = 0x7680;\n"
        )
        with self.assertRaises(RuntimeError):
            patch_legacy(source)


if __name__ == "__main__":
    unittest.main()
