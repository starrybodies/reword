"""Agent destination: text written for a model reader, checked for lost instructions."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import examples
import voice_context as voice
from reword import agent_instructions, build_request, check
from voice_learning import (apply_learning_proposal, build_learning_request, collection_status,
                            compile_profile)
from voice_store import add_feedback, add_sample, commit_profile, create_collection, save_collection

ASK = ("Hey, could you maybe take a look at `apps/web/checkout.tsx`? p95 went from 340 ms to 900 ms. "
       "Do NOT touch the payments module. Run `pnpm test checkout` first, and run `pnpm test checkout` again before you finish. Thanks!")
BRIEF = ("Find why `apps/web/checkout.tsx` got slower and report the cause. p95 went from 340 ms to 900 ms. "
         "Do not touch the payments module. Run `pnpm test checkout` before and after.")


class Resolution(unittest.TestCase):
    def test_agent_is_a_destination_with_its_own_card(self):
        resolved = voice.resolve_context("agent")
        self.assertEqual((resolved["destination"], resolved["source"]), ("agent", "explicit"))
        card = voice.render_style_card(resolved)
        self.assertLessEqual(len(card), 600)
        for required in ("model", "paths", "commands", "code", "URLs", "numbers", "Never invent a requirement"):
            self.assertIn(required, card)
        for absent in ("author character", "lowercase", "contractions"):
            self.assertNotIn(absent, card)

    def test_named_agent_context(self):
        card = voice.render_style_card(voice.resolve_context("agent/codex"))
        self.assertIn("Agent (codex):", card)
        self.assertLessEqual(len(card), 600)

    def test_inference_needs_the_artifact_named_not_the_topic(self):
        for context in ("Write a system prompt for support", "an agent brief for the migration",
                        "prompt for the coding agent", "subagent instructions"):
            with self.subTest(context=context):
                self.assertEqual(voice.resolve_context("auto", context=context)["destination"], "agent")
        for context, expected in (("LinkedIn post about AI agents", "linkedin"), ("Email about Claude Code", "email"),
                                  ("Notes on agents", "general")):
            with self.subTest(context=context):
                self.assertEqual(voice.resolve_context("auto", context=context)["destination"], expected)

    def test_aliases(self):
        for alias in ("prompt", "LLM", "system prompt", "ai_agent", "subagent"):
            with self.subTest(alias=alias):
                self.assertEqual(voice.resolve_context(alias)["destination"], "agent")


class Request(unittest.TestCase):
    def test_agent_kernel_replaces_the_prose_kernels(self):
        request = build_request(ASK, destination="agent")
        self.assertTrue(request["instructions"].startswith(agent_instructions()))
        self.assertEqual(request["meta"]["voice_guidance_mode"], "agent")
        self.assertNotIn("Genre:", request["instructions"])
        self.assertIn("Genre:", build_request(ASK, genre="technical", destination="agent")["instructions"])
        self.assertLessEqual(request["meta"]["guidance"]["characters"], 4000)

    def test_voice_traits_and_samples_never_reach_an_agent_request(self):
        profile = {"preferences": ["State the done condition last"], "avoid": ["Role-play framing"],
                   "traits": {"rhythm": "Long reflective turns"}, "samples": ["The kettle stopped. We kept talking."],
                   "preserve": ["payments module"]}
        request = build_request(ASK, profile=profile, destination="agent")
        self.assertEqual(request["input"]["voice"], {"preferences": ["State the done condition last"], "avoid": ["Role-play framing"]})
        self.assertNotIn("voice_samples", request["input"])
        self.assertEqual(request["input"]["preserve"], ["payments module"])
        self.assertTrue(request["instructions"].startswith(agent_instructions()))
        card = voice.compact_voice(profile, "agent")
        self.assertEqual(set(card), {"preferences", "avoid", "apply"})
        self.assertEqual(voice.compact_voice({"traits": {"rhythm": "Long reflective turns"}}, "agent"), {})

    def test_agent_examples_are_selected_only_for_agent_text(self):
        chosen = [entry["id"] for entry in examples.select_examples(ASK, destination="agent")]
        self.assertEqual(chosen, ["agent-request"])
        loud = "IMPORTANT!!! You MUST NEVER push to main."
        self.assertEqual([entry["id"] for entry in examples.select_examples(loud, destination="agent/codex")], ["agent-standing-rule"])
        self.assertEqual(examples.select_examples("Find why the build fails and report the cause.", destination="agent"), [])
        self.assertNotIn("agent-request", [entry["id"] for entry in examples.select_examples(ASK, destination="email")])

    def test_kernel_fits_the_default_guidance_budget_with_examples(self):
        self.assertLessEqual(len(agent_instructions()), 2200)
        request = build_request(ASK, destination="agent", audience="Coding agent in a pnpm monorepo",
                                purpose="Diagnose a regression", context="x" * 400)
        self.assertLessEqual(request["meta"]["guidance"]["characters"], 4000)


class Check(unittest.TestCase):
    def test_saying_a_literal_once_is_not_a_loss_for_an_agent(self):
        result = check(ASK, BRIEF, destination="agent")
        self.assertEqual(result["errors"], [])
        self.assertNotEqual(result["status"], "blocked")
        prose = check(ASK, BRIEF, destination="general")
        self.assertEqual(prose["status"], "blocked")
        self.assertNotIn("efficiency", prose)

    def test_losing_every_mention_still_blocks(self):
        dropped = BRIEF.replace(" Run `pnpm test checkout` before and after.", "").replace("from 340 ms to 900 ms", "sharply")
        result = check(ASK, dropped, destination="agent")
        self.assertEqual(result["status"], "blocked")
        kinds = {(error["kind"], error["change"]) for error in result["errors"]}
        self.assertIn(("inline-code", "removed"), kinds)
        self.assertIn(("number", "removed"), kinds)

    def test_invented_literals_block(self):
        result = check(ASK, BRIEF + " Keep p95 under 400 ms and edit `apps/web/cart.tsx` if needed.", destination="agent")
        self.assertEqual(result["status"], "blocked")
        added = {error["value"] for error in result["errors"] if error["change"] == "added"}
        self.assertIn("`apps/web/cart.tsx`", added)
        self.assertIn("400", added)

    def test_marking_an_existing_literal_as_code_is_not_an_addition(self):
        original = "Please run pnpm test checkout and tell me what fails."
        self.assertEqual(check(original, "Run `pnpm test checkout` and report what fails.", destination="agent")["errors"], [])
        self.assertEqual(check("Run `pnpm test checkout` now.", "Run pnpm test checkout now.", destination="agent")["errors"], [])
        blocked = check(original, "Run `pnpm test cart` and report what fails.", destination="agent")
        self.assertEqual(blocked["status"], "blocked")

    def test_efficiency_is_reported_and_growth_needs_review(self):
        saved = check(ASK, BRIEF, destination="agent")["efficiency"]
        self.assertGreater(saved["original"]["estimated_tokens"], saved["candidate"]["estimated_tokens"])
        self.assertEqual(saved["estimated_tokens_saved"], saved["original"]["estimated_tokens"] - saved["candidate"]["estimated_tokens"])
        self.assertGreater(saved["saved_percent"], 0)
        grown = check("Fix the flaky login test.", "Fix the flaky login test. Work carefully and think step by step about every case.", destination="agent")
        self.assertEqual(grown["status"], "review")
        self.assertEqual(grown["review"][0]["kind"], "length")
        self.assertLess(grown["efficiency"]["saved_percent"], 0)

    def test_locks_need_one_surviving_mention(self):
        original = "Never edit the payments module. Again: leave the payments module alone."
        self.assertEqual(check(original, "Never edit the payments module.", ["payments module"], destination="agent")["errors"], [])
        lost = check(original, "Never edit billing code.", ["payments module"], destination="agent")
        self.assertEqual([error["kind"] for error in lost["errors"]], ["locked-phrase"])


class Collections(unittest.TestCase):
    def store(self):
        store = create_collection("Synthetic writer")
        store = add_sample(store, "The kettle stopped. We kept talking. The rain did the rest.")
        request = build_learning_request(store)
        store = apply_learning_proposal(store, request, {
            "request_hash": request["input"]["request_hash"], "evidence_ids": request["input"]["evidence_ids"],
            "traits": {"rhythm": "Short sentences with a restrained landing"}})
        store = add_feedback(store, kind="preference", prefer=["UK spelling"])
        store = add_feedback(store, kind="preference", destination="agent", prefer=["State the done condition last"])
        return add_feedback(store, kind="preference", destination="agent/codex", avoid=["Role-play framing"])

    def test_agent_profile_carries_preferences_without_traits(self):
        profile = compile_profile(self.store(), "agent/codex")
        self.assertEqual(profile["preferences"], ["UK spelling", "State the done condition last"])
        self.assertEqual(profile["avoid"], ["Role-play framing"])
        self.assertNotIn("traits", profile)
        self.assertNotIn("avoid", compile_profile(self.store(), "agent"))

    def test_agent_destinations_take_no_samples_profiles_or_learning(self):
        store = self.store()
        for destination in ("agent", "agent/codex"):
            with self.subTest(destination=destination):
                with self.assertRaisesRegex(ValueError, "not writing samples"):
                    add_sample(store, "Find the bug and report it.", destination=destination)
                with self.assertRaisesRegex(ValueError, "no voice to learn"):
                    build_learning_request(store, destination)
                with self.assertRaisesRegex(ValueError, "no learned voice profile"):
                    commit_profile(store, destination, {"traits": {"rhythm": "Terse"}}, [], expected_revision=store["revision"])

    def test_agent_feedback_never_waits_on_a_refresh(self):
        store = add_feedback(self.store(), kind="revision", destination="agent", reason="Too long",
                             draft="Please kindly find the bug.", final="Find the bug.")
        status = collection_status(store)
        for destination in ("agent", "agent/codex"):
            self.assertEqual(status["destinations"][destination]["pending_eligible_count"], 0)
        self.assertEqual(status["pending_correction_evidence_ids"], [])
        agent_ids = {record["id"] for record in store["feedback"] if record["destination"].startswith("agent")}
        self.assertTrue(agent_ids <= set(status["feedback_only_pending_ids"]))
        general = build_learning_request(store, "general")
        self.assertFalse(agent_ids & set(general["input"]["evidence_ids"]))

    def test_prompt_with_a_collection_reports_explicit_basis(self):
        with tempfile.TemporaryDirectory() as directory:
            path, ask = Path(directory) / "voice.json", Path(directory) / "ask.md"
            save_collection(path, self.store(), create=True)
            ask.write_text(ASK + "\n", encoding="utf-8")
            variables = dict(os.environ)
            variables.pop("REWORD_VOICE", None)
            run = subprocess.run([sys.executable, str(ROOT / "scripts/reword.py"), "prompt", str(ask), "--voice", str(path),
                                  "--destination", "agent/codex"], text=True, capture_output=True, env=variables)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)
            status = result["meta"]["voice_collection"]
            self.assertEqual((status["basis"], status["needs_refresh"]), ("explicit-preferences", False))
            self.assertEqual(result["input"]["voice"]["avoid"], ["Role-play framing"])
            self.assertNotIn("traits", result["input"]["voice"])
            card = subprocess.run([sys.executable, str(ROOT / "scripts/reword.py"), "voice", "export", str(path),
                                   "--destination", "agent", "--format", "card"], text=True, capture_output=True, env=variables)
            self.assertTrue(card.stdout.startswith("Write for an agent reader."))
            self.assertNotIn("Rhythm:", card.stdout)


if __name__ == "__main__":
    unittest.main()
