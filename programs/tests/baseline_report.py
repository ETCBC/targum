"""Run the whole baseline suite as one report, then the gate.

    python programs/tests/baseline_report.py

This is the report form: every table in order, then the summary, then the gate, which
exits non-zero if any check failed. Under pytest the same measurements run as individual tests
and each one fails on its own account.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import baseline_corpus as C                                             # noqa: E402
import test_baseline_composition as composition                        # noqa: E402
import test_baseline_features as features                              # noqa: E402
import test_baseline_lexeme as lexeme                                  # noqa: E402
import test_baseline_provenance as provenance                          # noqa: E402
import test_baseline_register as register                              # noqa: E402
import test_baseline_structure as structure                            # noqa: E402

# Declaration order, which is also the order the report prints in. The dependencies between them
# are resolved by `C.once`, so this order is for the reader rather than for correctness.
STAGES = [
    ("PROVENANCE", provenance, ["the_dataset_is_current",
                                "the_feature_inventory_is_complete",
                                "the_feature_distribution_is_reported"]),
    ("COMPOSITION", composition, ["01_words_compose_the_word_group",
                                  "02_words_compose_the_segment",
                                  "03_word_groups_compose_the_verse_line",
                                  "04_segments_compose_the_verse_line",
                                  "05_words_compose_the_verse_line",
                                  "the_word_tier_offsets_resolve"]),
    ("FEATURES", features, ["06_ordinals_agree_with_node_order",
                            "07_the_etcbc_features_are_uppercase",
                            "08_the_lexeme_inventory_of_each_corpus",
                            "09_a_feature_name_means_one_thing",
                            "11_every_feature_counted_by_its_node_type",
                            "12_the_features_of_this_version"]),
    ("LEXEME", lexeme, ["13_the_lexeme_belongs_to_its_surface"]),
    ("STRUCTURE", structure, ["10_sections_are_determined",
                              "14_the_crossref_edge_is_the_address_relation",
                              "15_the_publication_key"]),
]


def main():
    C.setup()
    for label, module, names in STAGES:
        for name in names:
            print(f"\n{'=' * 78}\n{label}  {name}\n{'=' * 78}")
            getattr(module, f"run_{name}")()
    print(f"\n{'=' * 78}\nREGISTER\n{'=' * 78}")
    register.run_the_exclusion_register()
    print(f"\n{'=' * 78}\nSUMMARY\n{'=' * 78}")
    register.report_summary()
    print(f"\n{'=' * 78}\nGATE\n{'=' * 78}")
    return register.gate()


if __name__ == "__main__":
    sys.exit(main())
