import unittest
from typing import List, Dict

from models import UserAnswer, Profile
from scoring_engine import score_answers # Main function to test
from data_loader import ALL_ITEM_METADATA # To get all possible slots for generating test answers
from config import LIKERT_SCORE_MAP, REVERSE_ITEM_MAPPING, ALL_INSTINCTS, CREATION_INSTINCT_NAME
from data_loader import INSTINCT_TO_SUBTYPES_MAP

class TestScoringEngine(unittest.TestCase):

    def _generate_answers(self, likert_answer_text: str, scenario_answer_key: str = "A") -> List[UserAnswer]:
        """Helper to generate a full list of answers (100 items)."""
        answers: List[UserAnswer] = []
        for item_meta in ALL_ITEM_METADATA:
            if item_meta.answer_type == "Likert":
                answers.append(UserAnswer(slot=item_meta.slot, answer=likert_answer_text))
            elif item_meta.answer_type == "Scenario":
                # Ensure the scenario_answer_key is valid for the item's scenario_map
                # Defaulting to "A" if map exists, otherwise skipping (should not happen with full data)
                if item_meta.scenario_map and scenario_answer_key in item_meta.scenario_map:
                    answers.append(UserAnswer(slot=item_meta.slot, answer=scenario_answer_key))
                elif item_meta.scenario_map: # pick first available option if 'A' is not valid (e.g. if map was modified)
                    first_option = next(iter(item_meta.scenario_map.keys()))
                    answers.append(UserAnswer(slot=item_meta.slot, answer=first_option))
                # else: print(f"Warning: Scenario item {item_meta.slot} has no scenario_map or key {scenario_answer_key} is invalid for test generation.")
        return answers

    def test_all_strongly_agree(self):
        """Test with all Likert items as 'Strongly Agree' and scenarios as option 'A'."""
        answers = self._generate_answers(likert_answer_text="Strongly Agree", scenario_answer_key="A")
        self.assertEqual(len(answers), len(ALL_ITEM_METADATA), "Should generate one answer per item meta")
        
        profile = score_answers(answers)
        self.assertIsInstance(profile, Profile)
        # Add more specific assertions based on expected outcomes for "all strongly agree"
        # For example, non-reverse Likert items should give +1 to their subtype.
        # Reverse Likert items should NOT give +1 to their mapped subtype.
        # Scenario items with option "A" should give +1 to the mapped subtype.

        # Example: Check if a known non-reverse item's subtype got a point
        # ER-1 is Bursty (non-reverse). Strongly Agree should endorse Bursty.
        # This requires access to the intermediate raw_subtype_totals or more complex checks on final profile.
        # For now, focusing on the profile generation.
        self.assertIn(profile.driver, ALL_INSTINCTS)
        self.assertIn(profile.creation, INSTINCT_TO_SUBTYPES_MAP.get(CREATION_INSTINCT_NAME, []))

    def test_all_strongly_disagree(self):
        """Test with all Likert items as 'Strongly Disagree' and scenarios as option 'B' (or other)."""
        answers = self._generate_answers(likert_answer_text="Strongly Disagree", scenario_answer_key="B")
        self.assertEqual(len(answers), len(ALL_ITEM_METADATA))

        profile = score_answers(answers)
        self.assertIsInstance(profile, Profile)
        # Add more specific assertions based on expected outcomes for "all strongly disagree"
        # For example, non-reverse Likert items should NOT give +1 to their subtype.
        # Reverse Likert items SHOULD give +1 to their mapped subtype.

        self.assertIn(profile.driver, ALL_INSTINCTS)
        self.assertIn(profile.creation, INSTINCT_TO_SUBTYPES_MAP.get(CREATION_INSTINCT_NAME, []))

    def test_reverse_item_scoring_er5_steady(self):
        """Test a specific reverse item ER-5 (rewards Steady if user disagrees)."""
        # ER-5: "I struggle to stay engaged during extended, calm work sessions." (Reverse)
        # Rewards "Steady" if Likert <= 2 (e.g., Strongly Disagree)
        
        slot_to_test = "ER-5"
        target_subtype = REVERSE_ITEM_MAPPING.get(slot_to_test)
        self.assertEqual(target_subtype, "Steady", "Pre-condition: ER-5 should map to Steady")

        answers: List[UserAnswer] = []
        # Set all other answers to Neutral to isolate ER-5's impact
        for item_meta in ALL_ITEM_METADATA:
            if item_meta.slot == slot_to_test:
                answers.append(UserAnswer(slot=slot_to_test, answer="Strongly Disagree")) # Should endorse Steady
            elif item_meta.answer_type == "Likert":
                answers.append(UserAnswer(slot=item_meta.slot, answer="Neutral"))
            elif item_meta.answer_type == "Scenario":
                answers.append(UserAnswer(slot=item_meta.slot, answer="A")) # Arbitrary scenario choice
        
        profile = score_answers(answers)
        # This test is tricky without inspecting raw_subtype_totals directly.
        # We'd need to check if "Steady" has a higher score than if ER-5 was "Neutral" or "Strongly Agree".
        # A more direct way would be to test `calculate_subtype_endorsements` or `get_raw_subtype_totals`.
        # For now, we assert profile is generated. Deeper inspection requires more test setup or helper functions.
        self.assertIsInstance(profile, Profile)
        # A possible check: If Steady became dominant for Energy Rhythm or influenced Driver/Growth Edge.
        # This becomes an integration test for the scoring rules.

    def test_scenario_item_scoring_er6_option_a_bursty(self):
        """Test a specific scenario item ER-6, option A (rewards Bursty)."""
        slot_to_test = "ER-6"
        # ER-6 Option A maps to Bursty based on scenario_mapping.json

        answers: List[UserAnswer] = []
        for item_meta in ALL_ITEM_METADATA:
            if item_meta.slot == slot_to_test:
                answers.append(UserAnswer(slot=slot_to_test, answer="A")) # Should endorse Bursty
            elif item_meta.answer_type == "Likert":
                answers.append(UserAnswer(slot=item_meta.slot, answer="Neutral"))
            elif item_meta.answer_type == "Scenario": # Other scenario questions
                answers.append(UserAnswer(slot=item_meta.slot, answer="B")) # Arbitrary other choice
        
        profile = score_answers(answers)
        self.assertIsInstance(profile, Profile)
        # Similar to reverse items, checking dominant subtype or specific score for Bursty is needed for full validation.

    # TODO: Add more tests:
    # - Mixed answers leading to a known/expected profile (golden test case)
    # - Tie-breaking for Driver instinct
    # - Tie-breaking for Creation instinct (raw score, endorsed items, predefined order)
    # - Growth Edge selection logic
    # - Edge cases: empty answers list (though API layer should catch this)
    # - Test dominant subtype selection logic

if __name__ == '__main__':
    unittest.main() 