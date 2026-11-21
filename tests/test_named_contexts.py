"""Named contexts: any destination can carry author-defined contexts such as chat/family."""

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
from reword import build_request
from voice_learning import (apply_learning_proposal, build_learning_request, collection_status,
                            compile_profile, named_contexts)
from voice_store import add_feedback, add_sample, create_collection, save_collection, validate_collection


def learned(store, destination, traits):
    request = build_learning_request(store, destination)
    proposal = {"request_hash": request["input"]["request_hash"],
                "evidence_ids": request["input"]["evidence_ids"], "traits": traits}
    return apply_learning_proposal(store, request, proposal)


class Names(unittest.TestCase):
    def test_named_context_keeps_its_channel(self):
        for value, expected in (("chat/family", ("chat", "family")), ("web-copy/acme-2", ("web-copy", "acme-2")),
                                ("general/membership-application", ("general", "membership-application")),
                                ("email", ("email", ""))):
            with self.subTest(value=value):
                self.assertEqual(voice.split_destination(value), expected)
                self.assertEqual(voice.canonical_destination(value), value)
                self.assertEqual(voice.base_destination(value), expected[0])

    def test_malformed_names_are_rejected(self):
        for value in ("chat/", "/family", "chat/Family", "chat/family group", "chat/a/b", "nope/family",
                      "auto/family", "chat/-family", "chat/family-", "chat/" + "x" * 41, "", None, 7):
            with self.subTest(value=value), self.assertRaises(ValueError):
                voice.canonical_destination(value)

    def test_scopes_run_from_broad_to_specific(self):
        self.assertEqual(voice.destination_scopes("general"), ("general",))
        self.assertEqual(voice.destination_scopes("chat"), ("general", "chat"))
        self.assertEqual(voice.destination_scopes("chat/family"), ("general", "chat", "chat/family"))
        self.assertEqual(voice.destination_scopes("general/application"), ("general", "general/application"))


class Resolution(unittest.TestCase):
    def test_named_context_inherits_channel_defaults(self):
        named, channel = voice.resolve_context("chat/family"), voice.resolve_context("chat")
        self.assertEqual(named["destination"], "chat/family")
        self.assertEqual((named["source"], named["confidence"]), ("explicit", "explicit"))
        self.assertEqual(named["style"], channel["style"])
        self.assertEqual(named["guidance"], channel["guidance"])

    def test_preferences_layer_general_then_channel_then_named(self):
        preferences = {"general": {"regional_spelling": "UK", "contractions": "avoid"},
                       "chat": {"case": "sentence", "contractions": "natural"},
                       "chat/family": {"case": "lowercase"},
                       "chat/work": {"punctuation": "standard"}}
        family = voice.resolve_context("chat/family", preferences=preferences)["style"]
        self.assertEqual((family["case"], family["contractions"], family["regional_spelling"]), ("lowercase", "natural", "UK"))
        work = voice.resolve_context("chat/work", preferences=preferences)["style"]
        self.assertEqual((work["case"], work["punctuation"]), ("sentence", "standard"))
        override = voice.resolve_context("chat/family", preferences={**preferences, "case": "sentence"})["style"]
        self.assertEqual(override["case"], "sentence")

    def test_spacing_and_case_normalize_but_unknown_channels_fall_back(self):
        self.assertEqual(voice.resolve_context(" Chat/Family Group ")["destination"], "chat/family-group")
        self.assertEqual(voice.resolve_context("sms/family")["destination"], "text-message/family")
        for value in ("nope/family", "chat/", "chat/a/b"):
            with self.subTest(value=value):
                result = voice.resolve_context(value)
                self.assertEqual((result["destination"], result["source"]), ("general", "fallback"))

    def test_named_card_names_the_context_within_budget(self):
        card = voice.render_style_card(voice.resolve_context("web-copy/acme"))
        self.assertIn("Web copy (acme):", card)
        self.assertIn("named context", card)
        longest = {key: max(values, key=len) for key, values in voice.STYLE_CHOICES.items()}
        for destination in voice.DESTINATIONS:
            name = destination + "/" + "x" * voice.MAX_CONTEXT_NAME
            self.assertLessEqual(len(voice.render_style_card(voice.resolve_context(name, preferences=longest))), 600)

    def test_named_context_uses_its_channel_examples(self):
        text = "I am writing to inquire whether we are still meeting at 7."
        self.assertEqual(examples.select_examples(text, destination="chat/family"),
                         examples.select_examples(text, destination="chat"))


class Collections(unittest.TestCase):
    def store(self):
        store = create_collection("Synthetic writer")
        store = add_sample(store, "The kettle stopped. We kept talking. The rain did the rest.")
        store = add_sample(store, "ok so dinner is at 7, bring nothing, i mean it", destination="chat/family")
        store = add_sample(store, "Shipping the fix today. Review is open if anyone wants a look.", destination="chat/work")
        store = add_feedback(store, kind="preference", prefer=["Plain words over jargon"])
        store = add_feedback(store, kind="preference", destination="chat", prefer=["Keep messages to a few lines"])
        store = add_feedback(store, kind="preference", destination="chat/family", prefer=["Tease gently"], avoid=["Work vocabulary"])
        return store

    def test_store_accepts_named_contexts_and_rejects_malformed_ones(self):
        store = self.store()
        self.assertEqual(named_contexts(store), ["chat/family", "chat/work"])
        for destination in ("chat/Family", "nope/family", "chat/a/b"):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                add_sample(store, "A line.", destination=destination)
            with self.subTest(feedback=destination), self.assertRaises(ValueError):
                add_feedback(store, kind="preference", destination=destination, prefer=["Short lines"])

    def test_explicit_preferences_layer_and_stay_out_of_sibling_contexts(self):
        store = self.store()
        family = compile_profile(store, "chat/family")
        self.assertEqual(family["preferences"], ["Plain words over jargon", "Keep messages to a few lines", "Tease gently"])
        self.assertEqual(family["avoid"], ["Work vocabulary"])
        work = compile_profile(store, "chat/work")
        self.assertEqual(work["preferences"], ["Plain words over jargon", "Keep messages to a few lines"])
        self.assertNotIn("avoid", work)
        self.assertEqual(compile_profile(store, "chat")["preferences"], work["preferences"])

    def test_learned_traits_layer_general_then_channel_then_named(self):
        store = learned(self.store(), "general", {"rhythm": "Short sentences with a restrained landing",
                                                  "openings": "Open with a concrete detail"})
        store = learned(store, "chat/family", {"rhythm": "Loose lowercase run-ons with a dry aside"})
        family = compile_profile(store, "chat/family")
        self.assertEqual(family["traits"]["rhythm"], "Loose lowercase run-ons with a dry aside")
        self.assertEqual(family["traits"]["openings"], "Open with a concrete detail")
        self.assertEqual(compile_profile(store, "chat/work")["traits"]["rhythm"], "Short sentences with a restrained landing")
        self.assertEqual(set(store["profiles"]), {"general", "chat/family"})
        validate_collection(store)

    def test_named_learning_sees_its_own_and_broader_evidence_only(self):
        request = build_learning_request(self.store(), "chat/family")
        tags = {record["destination"] for record in request["input"]["evidence"]}
        self.assertEqual(tags, {"general", "chat", "chat/family"})
        channel = build_learning_request(self.store(), "chat")
        self.assertNotIn("chat/family", {record["destination"] for record in channel["input"]["evidence"]})

    def test_status_lists_named_contexts(self):
        status = collection_status(self.store())
        self.assertEqual(status["named_contexts"], ["chat/family", "chat/work"])
        self.assertIn("chat/family", status["destinations"])
        self.assertGreater(status["destinations"]["chat/family"]["pending_eligible_count"], 0)

    def test_request_carries_named_guidance(self):
        store = self.store()
        request = build_request("Dinner is at seven. Please bring nothing.", profile=compile_profile(store, "chat/family"),
                                destination="chat/family")
        self.assertEqual(request["meta"]["destination"]["destination"], "chat/family")
        self.assertIn("Chat (family):", request["instructions"])
        self.assertIn("Tease gently", request["input"]["voice"]["preferences"])


class CommandLine(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)

    def cli(self, *args):
        variables = dict(os.environ)
        variables.pop("REWORD_VOICE", None)
        return subprocess.run([sys.executable, str(ROOT / "scripts/reword.py"), *map(str, args)],
                              text=True, capture_output=True, env=variables)

    def test_collection_commands_accept_named_contexts(self):
        store, sample, draft = self.path / "voice.json", self.path / "sample.md", self.path / "draft.md"
        save_collection(store, create_collection("Synthetic writer"), create=True)
        sample.write_text("ok so dinner is at 7, bring nothing, i mean it\n", encoding="utf-8")
        draft.write_text("Dinner is at seven. Please bring nothing.\n", encoding="utf-8")
        added = self.cli("voice", "add", store, sample, "--destination", "chat/family")
        self.assertEqual(added.returncode, 0, added.stderr)
        saved = self.cli("voice", "feedback", store, "--kind", "preference", "--destination", "chat/family", "--prefer", "Tease gently")
        self.assertEqual(saved.returncode, 0, saved.stderr)
        self.assertEqual(json.loads(saved.stdout)["status"]["named_contexts"], ["chat/family"])
        prompt = self.cli("prompt", draft, "--voice", store, "--destination", "chat/family")
        self.assertEqual(prompt.returncode, 0, prompt.stderr)
        result = json.loads(prompt.stdout)
        self.assertEqual(result["meta"]["voice_collection"]["destination"], "chat/family")
        self.assertEqual(result["meta"]["voice_collection"]["named_contexts"], ["chat/family"])
        self.assertIn("Tease gently", result["input"]["voice"]["preferences"])
        card = self.cli("voice", "export", store, "--destination", "chat/family", "--format", "card")
        self.assertIn("Chat (family):", card.stdout)

    def test_malformed_named_context_is_a_usage_error(self):
        store = self.path / "voice.json"
        save_collection(store, create_collection("Synthetic writer"), create=True)
        result = self.cli("voice", "feedback", store, "--kind", "preference", "--destination", "chat/Family", "--prefer", "Short")
        self.assertEqual(result.returncode, 2)
        self.assertIn("named context", result.stderr)

    def test_legacy_profile_accepts_named_context_preferences(self):
        profile = self.path / "profile.json"
        self.assertEqual(self.cli("voice", "init", profile).returncode, 0)
        saved = self.cli("voice", "context", profile, "--destination", "linkedin/studio", "--contractions", "avoid")
        self.assertEqual(saved.returncode, 0, saved.stderr)
        style = self.cli("style", "--profile", profile, "--destination", "linkedin/studio")
        self.assertEqual(json.loads(style.stdout)["destination"]["style"]["contractions"], "avoid")
        self.assertEqual(json.loads(self.cli("style", "--profile", profile, "--destination", "linkedin").stdout)
                         ["destination"]["style"]["contractions"], "natural")


if __name__ == "__main__":
    unittest.main()
