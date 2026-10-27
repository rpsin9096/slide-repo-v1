"""v3.2: documentation claims must be checkable. (AUDIT A8, A9)"""
import os, re, subprocess, sys, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))


def read(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return f.read()


class TestDocsTruth(unittest.TestCase):
    def test_generated_cli_reference_is_current(self):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "gen_cli_docs.py"), "--check"])
        self.assertEqual(r.returncode, 0, "references/cli.md is stale: run scripts/gen_cli_docs.py --write")

    def test_skill_md_only_cites_registered_flags(self):
        import gen_cli_docs
        registered = set(gen_cli_docs.flags())
        cited = set(re.findall(r"(?<![\w-])--[a-z][a-z0-9-]+", read("SKILL.md")))
        self.assertEqual(sorted(cited - registered), [])

    def test_skill_md_frontmatter_and_size(self):
        text = read("SKILL.md")
        head = text.split("---")[1]
        self.assertIn("name: focus-gate", head)
        self.assertIn("description:", head)
        self.assertNotIn("disable-model-invocation", head)
        self.assertLess(len(text.splitlines()), 500)

    def test_every_loop_command_in_skill_md_is_in_the_help(self):
        out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "focus-gate.py"), "--help"],
                             capture_output=True, text=True).stdout
        for flag in ("--check", "--baseline", "--evidence", "--run", "--lint", "--init"):
            self.assertIn(flag, out)

    def test_no_doc_promises_tls(self):
        for doc in ("SPEC.md", "ARCHITECTURAL_BRAINSTORM.md", "SKILL.md"):
            self.assertNotRegex(read(doc), r"TLS-encrypted|optional TLS encryption")

    def test_audit_lists_open_items(self):
        self.assertIn("Open items", read("AUDIT.md"))


if __name__ == "__main__":
    unittest.main()
