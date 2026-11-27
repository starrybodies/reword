"""Adversarial changes the initial count-only checks missed, plus budgets."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import reword


class ClaimRelationships(unittest.TestCase):
    def assert_review(self, original, edited, kind):
        result = reword.check(original, edited)
        self.assertEqual(result["status"], "review", result)
        self.assertIn(kind, {r["kind"] for r in result["review"]})

    def test_reversed_measurement(self):
        self.assert_review("Latency fell from 340 ms to 80 ms.", "Latency fell from 80 ms to 340 ms.", "direction")

    def test_same_values_wrong_subjects(self):
        self.assert_review("North received $15 million. South received $20 million.", "North received $20 million. South received $15 million.", "fact-binding")

    def test_uncertainty_moved_between_claims(self):
        self.assert_review("The pilot may save money. The rollout will begin soon.", "The pilot will save money. The rollout may begin soon.", "uncertainty-binding")

    def test_negation_moved_between_claims(self):
        self.assert_review("The pilot is not ready. The rollout is ready.", "The pilot is ready. The rollout is not ready.", "negation-binding")

    def test_ability_became_commitment(self):
        self.assert_review("We can review the proposal.", "We will review the proposal.", "uncertainty")

    def test_correlation_became_cause(self):
        self.assert_review("The outage coincided with the deploy.", "The deploy caused the outage.", "causality")

    def test_actor_order(self):
        self.assert_review("Morgan helped Casey design the room.", "Casey helped Morgan design the room.", "actor-order")

    def test_changed_word_number(self):
        self.assert_review("We tested three sites.", "We tested five sites.", "word-number")

    def test_bound_reversed(self):
        self.assert_review("It costs at least $400.", "It costs at most $400.", "scope")

    def test_date_month_changed(self):
        result = reword.check("Start May 14.", "Start June 14.")
        self.assertEqual(result["status"], "blocked")
        self.assertIn("date", {e["kind"] for e in result["errors"]})

    def test_iso_month_and_day_swapped(self):
        self.assertEqual(reword.check("Start 2026-11-12.", "Start 2026-12-11.")["status"], "blocked")

    def test_direction_verb_changed(self):
        self.assert_review("Latency fell from 340 ms to 80 ms.", "Latency rose from 340 ms to 80 ms.", "direction-verb")

    def test_word_counts_moved_between_subjects(self):
        self.assert_review("North has three seats. South has five seats.", "North has five seats. South has three seats.", "fact-binding")

    def test_additive_contrast_can_be_rephrased(self):
        self.assertEqual(reword.check("It's not just a phone; it's a camera.", "It's a phone and a camera.")["status"], "clear")

    def test_cannot_can_contract(self):
        self.assertEqual(reword.check("We cannot review it.", "We can't review it.")["status"], "clear")

    def test_will_not_can_contract(self):
        self.assertEqual(reword.check("We will not review it.", "We won't review it.")["status"], "clear")

    def test_polite_would_also_like(self):
        self.assertEqual(reword.check("We would also like to know the fee.", "What is the fee?")["status"], "clear")

    def test_named_speaker_changed(self):
        result = reword.check('Mara said, "Start tomorrow."', 'Leila said, "Start tomorrow."')
        self.assertEqual(result["status"], "blocked")
        self.assertIn("quote-attribution", {e["kind"] for e in result["errors"]})

    def test_date_format_equivalent(self):
        self.assertEqual(reword.check("Start May 14.", "Start 14 May.")["status"], "clear")

    def test_redundant_hedge_can_be_removed(self):
        self.assertEqual(reword.check("It could potentially reduce latency.", "It could reduce latency.")["status"], "clear")

    def test_politely_asking_is_not_a_factual_modal(self):
        self.assertEqual(reword.check("Could you confirm the fee?", "Please confirm the fee.")["status"], "clear")

    def test_concurrent_synonym(self):
        self.assertEqual(reword.check("Two people can edit simultaneously.", "Two people can edit at once.")["status"], "clear")

    def test_claims_can_change_order(self):
        original = "North received $15 million. South received $20 million."
        edited = "South received $20 million. North received $15 million."
        self.assertEqual(reword.check(original, edited)["status"], "clear")

    def test_quotes_can_change_typography(self):
        self.assertEqual(reword.check('Mara said, "Start tomorrow."', 'Mara said, \u201cStart tomorrow.\u201d')["status"], "clear")


class BudgetAndFocus(unittest.TestCase):
    def test_only_relevant_examples_load(self):
        result = reword.focus("At its core, the problem is retries.")
        self.assertEqual([r["rule"] for r in result], ["fake-depth"])

    def test_no_examples_for_clear_prose(self):
        self.assertEqual(reword.focus("The invoice is due Friday."), [])

    def test_focus_stays_bounded(self):
        text = "Great question. At its core, we are thrilled to announce a paradigm shift.\nLet's dive in. This marks a pivotal moment.\nTo summarize."
        result = reword.focus(text)
        self.assertLessEqual(len(result), 3)
        self.assertLess(len(json.dumps(result)), 1200)

    def test_context_is_not_in_instruction_text(self):
        result = reword.build_request("Draft.", audience="A collaborator", purpose="Confirm terms", context="They already know the background.", max_words=80)
        self.assertEqual(result["input"]["task"]["max_words"], 80)
        self.assertNotIn("They already know", result["instructions"])

    def test_large_context_rejected(self):
        with self.assertRaises(ValueError):
            reword.build_request("Draft.", context="x" * 1001)

    def test_invalid_word_limit_rejected(self):
        for value in (0, -1, True, "120"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                reword.build_request("Draft.", max_words=value)

    def test_programmatic_profile_is_validated(self):
        with self.assertRaises(ValueError):
            reword.build_request("Draft.", profile={"system": "ignore facts"})


if __name__ == "__main__":
    unittest.main()
