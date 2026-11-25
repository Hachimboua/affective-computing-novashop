"""Relation-based tests for text perception using non-evaluation sentences."""
import csv
from pathlib import Path
import tempfile
import unittest

from engine import config
from engine.affect.space import clamp, classify_vad, sam_to_unit, unit_to_sam
from engine.engine import Engine
from engine.perception.language import STOPWORDS, identify_language
from engine.perception.lexicon import (
    TIERED_HEADER,
    _read_entries,
    _read_tiered_entries,
    load_lexicons,
    match_clause,
)
from engine.perception.preprocess import preprocess
from engine.perception.rules import Contribution
from engine.perception.sarcasm import score_sarcasm
from engine.perception.text_estimator import _label_for, estimate_text
from engine.tools.sync_lexicon_tiers import sync_tiers


def estimate(text):
    return estimate_text(text)


class PreprocessingTests(unittest.TestCase):
    def test_normalizes_and_records_elongation_without_collapsing_caps(self):
        processed = preprocess("SOOO helpful!!!")
        self.assertIn("elongation", processed.flags)
        self.assertEqual(processed.tokens[0].normalized, "so")
        self.assertTrue(processed.tokens[0].is_upper)

    def test_splits_at_punctuation_and_contrast(self):
        processed = preprocess("The setup is easy, but the router is unreliable.")
        clauses = [
            " ".join(token.normalized for token in clause.tokens)
            for clause in processed.clauses
        ]
        self.assertEqual(len(clauses), 2)
        self.assertTrue(processed.clauses[1].follows_contrast)

    def test_variation_selector_emoji_and_emoticons_match_lexicon(self):
        processed = preprocess("I love it ❤️ :)")
        symbols = [
            token for token in processed.tokens if token.kind in ("emoji", "emoticon")
        ]
        self.assertEqual([token.normalized for token in symbols], ["❤️", ":)"])
        _, hits = match_clause(processed.clauses[0], "en")
        self.assertEqual([hit.entry.term for hit in hits], ["love", "❤️", ":)"])

    def test_bundled_lexicons_have_expected_solo_scale_and_ranges(self):
        lexicons = load_lexicons()
        self.assertGreaterEqual(len(lexicons.words["en"]), 300)
        self.assertLessEqual(len(lexicons.words["en"]), 500)
        self.assertGreaterEqual(len(lexicons.words["pt"]), 100)
        self.assertLessEqual(len(lexicons.words["pt"]), 150)
        for entries in (
            lexicons.words["en"],
            lexicons.words["pt"],
            lexicons.phrases["en"],
            lexicons.phrases["pt"],
            lexicons.emojis,
        ):
            for entry in entries.values():
                self.assertTrue(
                    all(
                        -1.0 <= value <= 1.0
                        for value in (entry.valence, entry.activity, entry.dominance)
                    )
                )
        for entries in (lexicons.words["en"], lexicons.words["pt"]):
            for term in entries:
                self.assertGreater(len(term), 2)
                self.assertNotIn(term, STOPWORDS["en"] | STOPWORDS["pt"])

    def test_tier_values_match_the_configured_table(self):
        self.assertEqual(
            config.TIER_VAD,
            {
                "ANGER_STRONG": (-0.85, 0.80, 0.40),
                "ANGER": (-0.70, 0.60, 0.30),
                "FRUSTRATION": (-0.55, 0.35, 0.10),
                "PROBLEM_MILD": (-0.35, 0.15, 0.00),
                "PROBLEM": (-0.50, 0.20, 0.00),
                "FEAR": (-0.60, 0.55, -0.50),
                "SADNESS": (-0.60, -0.35, -0.35),
                "FATIGUE": (-0.45, -0.60, -0.30),
                "NEUTRAL": (0.00, 0.00, 0.00),
                "CONTENT": (0.45, -0.45, 0.25),
                "POSITIVE": (0.50, 0.10, 0.25),
                "JOY": (0.80, 0.55, 0.40),
            },
        )

    def test_tiered_loader_uses_config_and_partial_overrides(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tiered.tsv"
            path.write_text(
                "\t".join(TIERED_HEADER)
                + "\n"
                + "term\tPOSITIVE\t-0.10\t\t0.50\n",
                encoding="utf-8",
            )
            entry = _read_tiered_entries(path)["term"]
        self.assertEqual(entry.tier, "POSITIVE")
        self.assertEqual(
            (entry.valence, entry.activity, entry.dominance),
            (-0.10, 0.10, 0.50),
        )

    def test_tier_sync_prefers_my_tier_and_preserves_overrides(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            lexicon_dir = root / "lexicons"
            lexicon_dir.mkdir()
            entries = {
                "en.tsv": ("word", "PROBLEM_MILD", "ANGER"),
                "pt.tsv": ("palavra", "NEUTRAL", ""),
                "phrases_en.tsv": ("some phrase", "POSITIVE", ""),
                "phrases_pt.tsv": ("outra frase", "CONTENT", ""),
            }
            for filename, (term, tier, _) in entries.items():
                overrides = ("-0.20", "", "") if filename == "en.tsv" else ("", "", "")
                (lexicon_dir / filename).write_text(
                    "\t".join(TIERED_HEADER)
                    + "\n"
                    + "\t".join((term, tier) + overrides)
                    + "\n",
                    encoding="utf-8",
                )
            sheet_path = root / "review.csv"
            with sheet_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream,
                    fieldnames=("Lexicon", "term", "suggested tier", "my tier"),
                )
                writer.writeheader()
                for filename, (term, suggestion, my_tier) in entries.items():
                    writer.writerow(
                        {
                            "Lexicon": filename,
                            "term": term,
                            "suggested tier": suggestion,
                            "my tier": my_tier,
                        }
                    )

            synced = sync_tiers(sheet_path, lexicon_dir)
            updated_en = (lexicon_dir / "en.tsv").read_text(
                encoding="utf-8"
            ).splitlines()[1].split("\t")
            updated_pt = (lexicon_dir / "pt.tsv").read_text(
                encoding="utf-8"
            ).splitlines()[1].split("\t")
            updated_phrase_en = (lexicon_dir / "phrases_en.tsv").read_text(
                encoding="utf-8"
            ).splitlines()[1].split("\t")

        self.assertEqual(synced, 4)
        self.assertEqual(updated_en[1:], ["ANGER", "-0.20", "", ""])
        self.assertEqual(updated_pt[1], "NEUTRAL")
        self.assertEqual(updated_phrase_en[1], "POSITIVE")

    def test_sync_accepts_semicolon_separated_sheet_with_bom(self):
        """Excel on Portuguese Windows saves 'CSV UTF-8' with ';' separators."""
        from engine.tools.sync_lexicon_tiers import detect_delimiter
        self.assertEqual(detect_delimiter("Lexicon;term;suggested tier;my tier"), ";")
        self.assertEqual(detect_delimiter("Lexicon,term,suggested tier,my tier"), ",")
        self.assertEqual(detect_delimiter("Lexicon\tterm\tsuggested tier\tmy tier"), "\t")

    def test_loader_rejects_question_marks_and_replacement_characters(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.tsv"
            for invalid in ("term\x3fbad", "term\ufffdbad"):
                with self.subTest(invalid=invalid):
                    path.write_text(
                        "%s\t0.10\t0.20\t0.30\n" % invalid,
                        encoding="utf-8",
                    )
                    with self.assertRaises(ValueError):
                        _read_entries(path)
                    path.write_text(
                        "%s\tNEUTRAL\t\t\t\n" % invalid,
                        encoding="utf-8",
                    )
                    with self.assertRaises(ValueError):
                        _read_tiered_entries(path)

    def test_corrected_portuguese_words_and_phrases_match(self):
        processed = preprocess(
            "péssimo inaceitável não chegou está tudo resolvido"
        )
        _, hits = match_clause(processed.clauses[0], "pt")
        self.assertEqual(
            [hit.entry.term for hit in hits],
            ["péssimo", "inaceitável", "não chegou", "está tudo resolvido"],
        )

    def test_english_phrase_fragments_are_matched_as_phrases(self):
        examples = (
            ("well done", "well done"),
            ("good job", "good job"),
            ("thanks a ton", "thanks a ton"),
            ("thanks heaps", "thanks heaps"),
            ("worked perfectly", "worked perfectly"),
            ("great customer service", "great customer service"),
            ("good news", "good news"),
            ("arrived on time", "arrived on time"),
            ("delivered quickly", "delivered quickly"),
            ("dead on arrival", "dead on arrival"),
        )
        lexicons = load_lexicons()
        for fragment in ("a", "well", "done", "job", "ton", "heaps", "worked", "kind"):
            self.assertNotIn(fragment, lexicons.words["en"])
        for neutral_fragment in (
            "customer",
            "service",
            "news",
            "quickly",
            "promptly",
            "arrived",
            "delivered",
            "replacement",
        ):
            self.assertNotIn(neutral_fragment, lexicons.words["en"])
        for invented_form in (
            "perfectness",
            "wonderfulness",
            "amazingness",
            "brilliantest",
            "furiousness",
            "annoyingness",
            "incompetentness",
            "delightedly",
            "exhaustedness",
            "disappointedly",
            "inconvenientness",
            "mediocrely",
            "notideal",
        ):
            self.assertNotIn(invented_form, lexicons.words["en"])
        for text, expected in examples:
            with self.subTest(phrase=expected):
                processed = preprocess(text)
                _, hits = match_clause(processed.clauses[0], "en", lexicons)
                self.assertEqual([hit.entry.term for hit in hits], [expected])
        for word in ("fine", "disgrace", "wow"):
            self.assertIn(word, lexicons.words["en"])
        self.assertLess(lexicons.words["en"]["relaxed"].activity, 0.0)

    def test_neutral_shop_words_have_neutral_valence(self):
        lexicons = load_lexicons()
        for language in ("en", "pt"):
            for term in ("order", "service", "customer", "delivery", "arrived", "package"):
                entry = lexicons.words[language].get(term)
                if entry is not None:
                    with self.subTest(language=language, term=term):
                        self.assertLessEqual(abs(entry.valence), 0.2)


class TextEstimateTests(unittest.TestCase):
    def assert_new_sentences(self, sentences):
        messages_path = (
            Path(__file__).resolve().parent.parent
            / "engine"
            / "evaluation"
            / "data"
            / "messages.csv"
        )
        with messages_path.open("r", encoding="utf-8", newline="") as stream:
            evaluation_texts = {row["text"] for row in csv.DictReader(stream)}
        self.assertFalse(
            set(sentences).intersection(evaluation_texts),
            "Regression sentences must be absent from messages.csv",
        )

    def test_supported_language_regression_sentences(self):
        english = (
            "Great, it works now. Thanks!",
            "Wonderful news, the refund arrived.",
            "Oh wonderful, the tablet broke again. Fantastic.",
            "Everything is fine, no rush at all.",
            "I AM FURIOUS, THIS IS A DISGRACE!!!",
            "The printer worked perfectly after I cleaned the rollers.",
            "My tea tastes surprisingly pleasant this morning.",
            "We found the missing button beneath the cushion.",
            "You made the instructions clear and concise.",
            "It is quite pleasant to hear the birds outside.",
            "The old lamp casts a warm, gentle light.",
            "I appreciate your thoughtful message.",
            "That soup smells delicious and comforting.",
            "The garden looks lovely after the rain.",
            "The screen became bright after the update.",
            "He feels nervous before the concert.",
            "I am disappointed by this slow response.",
            "This service is remarkably helpful.",
            "The music sounds cheerful and lively.",
            "I cannot stand this constant buzzing.",
            "The instructions were confusing but the result was acceptable.",
            "We are grateful for the quick explanation.",
            "My order arrived earlier than expected.",
            "The package feels light and sturdy.",
            "Today has been exhausting and unpleasant.",
            "I feel hopeful about the new plan.",
            "The queue is long, but everyone seems patient.",
            "Your advice was useful and reassuring.",
            "The keyboard feels comfortable beneath my hands.",
            "The whole process was straightforward.",
        )
        portuguese = (
            "O café está quente e muito saboroso.",
            "Estou contente com a ajuda recebida.",
            "A resposta foi clara e bastante útil.",
            "Não fiquei satisfeito com a cobrança.",
            "A encomenda chegou antes do prazo previsto.",
            "O atendimento foi gentil e eficiente.",
            "Fiquei preocupado com o atraso da entrega.",
            "A tela está brilhante, mas o som parece fraco.",
            "Adorei a maneira como explicaram o processo.",
            "A situação parece difícil, porém ainda há esperança.",
            "O produto é leve e fácil de transportar.",
            "Estou muito frustrada com a falha repetida.",
            "A música deixou a sala tranquila e acolhedora.",
            "Meu cartão foi recusado, mas já consegui resolver.",
            "A entrega foi péssima e totalmente inaceitável.",
        )
        self.assertEqual(len(english), 30)
        self.assertEqual(len(portuguese), 15)
        self.assert_new_sentences(english + portuguese)
        for language, sentences in (("en", english), ("pt", portuguese)):
            for text in sentences:
                with self.subTest(language=language, text=text):
                    detected, _, flags = identify_language(preprocess(text).tokens)
                    self.assertEqual(detected, language)
                    self.assertNotIn("unsupported_language", flags)

    def test_phrase_hits_can_identify_the_supported_language(self):
        examples = (("Well done.", "en"), ("Está tudo resolvido.", "pt"))
        self.assert_new_sentences([text for text, _ in examples])
        for text, expected in examples:
            with self.subTest(expected=expected):
                detected, _, flags = identify_language(preprocess(text).tokens)
                self.assertEqual(detected, expected)
                self.assertNotIn("unsupported_language", flags)

    def test_canonical_english_and_portuguese_valence_signs(self):
        self.assert_new_sentences(
            (
                "I AM FURIOUS, THIS IS A DISGRACE!!!",
                "A entrega foi péssima e totalmente inaceitável.",
                "Tenho esperança.",
                "Sinto desesperança.",
            )
        )
        self.assertLess(
            estimate("I AM FURIOUS, THIS IS A DISGRACE!!!").valence, 0.0
        )
        self.assertLess(
            estimate("A entrega foi péssima e totalmente inaceitável.").valence,
            0.0,
        )
        self.assertGreater(estimate("Tenho esperança.").valence, 0.0)
        self.assertLess(estimate("Sinto desesperança.").valence, 0.0)

    def test_reviewed_low_energy_terms_need_negative_activity(self):
        lexicons = load_lexicons()
        for term in ("disappointed", "exhausted", "calm", "relieved"):
            with self.subTest(term=term):
                self.assertLess(lexicons.words["en"][term].activity, 0.0)

    def test_furious_must_be_more_negative_than_slow(self):
        words = load_lexicons().words["en"]
        self.assertLess(words["furious"].valence, words["slow"].valence)

    def test_labels_use_only_the_kits_emotion_vocabulary(self):
        labels = {
            _label_for(0.0, 0.0, 0.0),
            _label_for(0.7, -0.1, 0.0),
            _label_for(0.7, 0.7, 0.0),
            _label_for(-0.7, 0.7, 0.4),
            _label_for(-0.7, 0.7, -0.4),
            _label_for(-0.7, -0.5, 0.0),
            _label_for(-0.7, 0.0, 0.0),
        }
        self.assertEqual(
            labels,
            {"neutral", "calm", "joy", "anger", "frustration", "fear", "sadness"},
        )

    def test_prototype_points_map_to_their_own_labels(self):
        for label, point in config.LABEL_PROTOTYPES.items():
            with self.subTest(label=label):
                self.assertEqual(_label_for(*point), label)

    def test_neutral_radius_and_runner_up_distances(self):
        result = classify_vad(0.01, -0.02, 0.01)
        self.assertEqual(result["label"], "neutral")
        self.assertIsNotNone(result["second_label"])
        self.assertAlmostEqual(result["label_distance"], (0.00055) ** 0.5)
        self.assertGreater(result["second_distance"], result["label_distance"])

    def test_added_prototype_can_be_selected(self):
        prototypes = dict(config.LABEL_PROTOTYPES)
        prototypes["curious"] = (0.25, 0.30, 0.15)
        result = classify_vad(0.25, 0.30, 0.15, prototypes)
        self.assertEqual(result["label"], "curious")

    def test_sam_conversion_and_clamping(self):
        for rating in (1, 3, 5, 7, 9):
            self.assertAlmostEqual(unit_to_sam(sam_to_unit(rating)), rating)
        self.assertEqual(sam_to_unit(10), 1.25)
        self.assertEqual(unit_to_sam(1.25), 10.0)
        self.assertEqual(clamp(-4), -1.0)
        self.assertEqual(clamp(4), 1.0)

    def test_phase_three_sentences_map_to_expected_labels(self):
        examples = (
            ("this keeps happening, it's getting irritating", "frustration"),
            ("No worries, I'm relaxed about it", "calm"),
            ("I'm exhausted and sad about this", "sadness"),
            ("I'm terrified my card was stolen", "fear"),
            ("I AM FURIOUS!!!", "anger"),
            ("I love it, best purchase ever!", "joy"),
            ("What is the warranty period?", "neutral"),
        )
        self.assert_new_sentences([text for text, _ in examples])
        for text, expected in examples:
            with self.subTest(text=text):
                self.assertEqual(estimate(text).label, expected)

    def test_phase_three_generalization_labels(self):
        examples = (
            ("The repeated billing error is wearing me down.", "sadness"),
            ("I feel peaceful now that the parcel is here.", "calm"),
            ("I'm delighted with how sturdy this mug feels.", "joy"),
            ("This makes me furious; the seal was broken twice.", "anger"),
            ("I'm worried that my payment details are exposed.", "fear"),
            ("I feel drained after waiting through another long queue.", "sadness"),
            ("Could you explain the warranty coverage?", "neutral"),
            ("It's mildly annoying that the receipt is missing again.", "frustration"),
            ("Fiquei muito feliz com a ajuda recebida!", "joy"),
            ("Fiquei contente com o resultado, sem qualquer pressa.", "calm"),
            ("Estou cansado de repetir o mesmo pedido.", "sadness"),
            ("Tenho medo de uma cobranca duplicada.", "fear"),
            ("Estou furioso com o segundo erro na fatura.", "anger"),
            ("A embalagem chegou amassada e fiquei desanimada.", "sadness"),
            ("Qual e o prazo da garantia deste aparelho?", "neutral"),
        )
        self.assert_new_sentences([text for text, _ in examples])
        for text, expected in examples:
            with self.subTest(text=text):
                result = estimate(text)
                self.assertEqual(result.label, expected)
                self.assertTrue(
                    all(
                        -1.0 <= value <= 1.0
                        for value in (
                            result.valence,
                            result.activity,
                            result.dominance,
                        )
                    )
                )

    def test_delivery_problem_cues_are_negative_in_both_languages(self):
        examples = (
            "My parcel was supposed to be here and has not arrived.",
            "A encomenda devia chegar hoje e nunca chegou.",
        )
        self.assert_new_sentences(examples)
        for text in examples:
            with self.subTest(text=text):
                result = estimate(text)
                self.assertLess(result.valence, 0.0)
                self.assertIn("negative_event", result.flags)

    def test_negation_shifts_polarity_without_a_full_flip(self):
        good = estimate("good")
        not_good = estimate("not good")
        bad = estimate("bad")
        not_bad = estimate("not bad")
        self.assertGreater(good.valence, 0.0)
        self.assertLess(not_good.valence, good.valence)
        self.assertLess(not_good.valence, 0.1)
        self.assertGreater(not_bad.valence, bad.valence)

    def test_intensifiers_and_downtoners_change_strength(self):
        bad = estimate("bad")
        very_bad = estimate("very bad")
        slightly_bad = estimate("slightly bad")
        self.assertGreater(abs(very_bad.valence), abs(bad.valence))
        self.assertLess(abs(slightly_bad.valence), abs(bad.valence))
        self.assertIn("intensifier", very_bad.flags)
        self.assertIn("downtoner", slightly_bad.flags)

    def test_caps_and_punctuation_raise_activity(self):
        plain = estimate("i am furious")
        shouted = estimate("I'M FURIOUS!!!")
        self.assertGreater(shouted.activity, plain.activity)

    def test_sarcasm_matches_negative_forms_and_repetition_cues(self):
        positive = Contribution("bright", 0.8, 0.2, 0.2, 1.0, [])
        examples = (
            "The battery broke during transport.",
            "The latch breaks every morning.",
            "The screen is broken again.",
            "The kiosk stopped working overnight.",
            "The parcel never arrived at the depot.",
            "The forecast changed again.",
            "Another sunny afternoon is expected.",
            "The machine is still running smoothly.",
        )
        self.assert_new_sentences(examples)
        for text in examples:
            with self.subTest(text=text):
                score = score_sarcasm(text, [positive], "en")
                self.assertGreaterEqual(score, config.SARCASM_THRESHOLD)

    def test_additional_english_and_portuguese_sarcasm_idioms(self):
        examples = (
            ("Era só o que faltava.", "pt"),
            ("Só que não.", "pt"),
        )
        self.assert_new_sentences(
            [text for text, _ in examples] + ["I love that for me."]
        )
        for text, language in examples:
            with self.subTest(language=language):
                score = score_sarcasm(text, [], language)
                self.assertGreaterEqual(score, config.SARCASM_THRESHOLD)
        result = estimate("I love that for me.")
        self.assertIn("possible_sarcasm", result.flags)
        self.assertLess(result.valence, 0.0)

    def test_mixed_clauses_set_flag_and_later_clause_has_more_weight(self):
        result = estimate("The setup was easy but the router is terrible.")
        reversed_result = estimate("The router is terrible but the setup was easy.")
        self.assertLess(result.valence, 0.0)
        self.assertLess(result.valence, reversed_result.valence)
        self.assertIn("mixed_emotion", result.flags)
        self.assertIn("contrast", result.flags)

    def test_portuguese_text_gets_supported_language_and_negative_valence(self):
        result = estimate("O meu dispositivo está avariado e fiquei dececionada.")
        self.assertEqual(result.language, "pt")
        self.assertLess(result.valence, 0.0)

    def test_unsupported_script_is_flagged_and_confidence_is_capped(self):
        result = estimate("Где находится мой смартфон?")
        self.assertIn("unsupported_language", result.flags)
        self.assertLessEqual(result.confidence, config.UNSUPPORTED_CONFIDENCE_CAP)
        language, _, flags = identify_language(
            preprocess("Здравствуйте, wonderful!").tokens
        )
        self.assertEqual(language, "en")
        self.assertNotIn("unsupported_language", flags)

    def test_unsupported_latin_languages_are_flagged(self):
        examples = (
            ("Vorrei parlare con qualcuno riguardo alla mia fattura scaduta.", "unknown"),
            ("Bitte prüfen Sie meine Bestellung, bevor die Rechnung eintrifft.", "de"),
        )
        for text, expected_language in examples:
            with self.subTest(text=text):
                result = estimate(text)
                self.assertEqual(result.language, expected_language)
                self.assertIn("unsupported_language", result.flags)
                self.assertLessEqual(
                    result.confidence, config.UNSUPPORTED_CONFIDENCE_CAP
                )

    def test_all_caps_english_terms_remain_supported(self):
        examples = (
            ("UNBELIEVABLE!!!", "unbelievable"),
            ("THIS IS RIDICULOUS!!!", "ridiculous"),
            ("THIS IS ABSURD!!!", "absurd"),
            ("THIS IS NONSENSE!!!", "nonsense"),
            ("THIS IS A JOKE!!!", "this is a joke"),
        )
        self.assert_new_sentences([text for text, _ in examples])
        lexicons = load_lexicons()
        for text, expected_term in examples:
            with self.subTest(text=text):
                processed = preprocess(text)
                language, _, flags = identify_language(processed.tokens)
                self.assertEqual(language, "en")
                self.assertNotIn("unsupported_language", flags)
                _, hits = match_clause(processed.clauses[0], language, lexicons)
                self.assertIn(expected_term, [hit.entry.term for hit in hits])

    def test_a3_generalization_corpus(self):
        short_english = (
            "Not again!",
            "Wait, what?",
            "This again?",
            "Are we?",
            "What now?",
        )
        short_portuguese = (
            "E agora?",
            "Não sei.",
            "Que pena!",
            "Por quê?",
            "Já chegou?",
        )
        short_latin = ("wut", "huh?", "bruh", "blah")
        shouted_english = (
            "I AM OUTRAGED!!!",
            "THIS IS DISGUSTING!!!",
            "WHAT A DISGRACE!!!",
        )
        shouted_portuguese = (
            "ESTOU FURIOSO COM A DEMORA!!!",
            "ISTO É PÉSSIMO!!!",
        )
        corpus = (
            short_english
            + short_portuguese
            + short_latin
            + shouted_english
            + shouted_portuguese
        )
        self.assert_new_sentences(corpus)

        for language, sentences in (
            ("en", short_english + shouted_english),
            ("pt", short_portuguese + shouted_portuguese),
        ):
            for text in sentences:
                with self.subTest(language=language, text=text):
                    detected, _, flags = identify_language(
                        preprocess(text).tokens
                    )
                    self.assertEqual(detected, language)
                    self.assertNotIn("unsupported_language", flags)

        for text in short_latin:
            with self.subTest(text=text):
                result = Engine().process(text)
                self.assertIn("short_message", result["flags"])
                self.assertNotIn("unsupported_language", result["flags"])
                self.assertEqual(result["action"], "ASK_CLARIFICATION")
                self.assertNotIn(
                    "Please write in one of those languages.", result["reply"]
                )

    def test_foreign_stopwords_override_borrowed_english_phrase(self):
        examples = (
            ("Ich bin great customer service.", "de"),
            ("Je suis great customer service.", "fr"),
            ("Ik ben great customer service.", "nl"),
        )
        self.assert_new_sentences([text for text, _ in examples])
        for text, language in examples:
            with self.subTest(language=language):
                result = estimate(text)
                self.assertEqual(result.language, language)
                self.assertIn("unsupported_language", result.flags)

    def test_neutral_intent_has_moderate_confidence(self):
        result = estimate("Where is my order 48213?")
        self.assertEqual(result.intent, "ORDER_STATUS")
        self.assertEqual(result.entities.get("order_number"), "48213")
        self.assertGreaterEqual(result.confidence, 0.45)

    def test_empty_short_and_unknown_inputs_do_not_crash(self):
        for text in ("", "ok", "?"):
            with self.subTest(text=text):
                result = estimate(text)
                self.assertIn("short_message", result.flags)
                self.assertLessEqual(result.confidence, config.LOW_CONFIDENCE_THRESHOLD)

    def test_engine_contract_and_reset_are_deterministic(self):
        engine = Engine()
        first = engine.process("That was extremely helpful!")
        engine.reset()
        second = engine.process("That was extremely helpful!")
        first_comparable = dict(first)
        second_comparable = dict(second)
        first_comparable["details"] = dict(first["details"])
        second_comparable["details"] = dict(second["details"])
        first_comparable["details"].pop("timing_ms")
        second_comparable["details"].pop("timing_ms")
        self.assertEqual(first_comparable, second_comparable)
        for key in (
            "valence",
            "activity",
            "confidence",
            "label",
            "action",
            "reply",
            "dominance",
            "flags",
            "details",
        ):
            self.assertIn(key, first)
        for key in ("second_label", "label_distance", "second_distance"):
            self.assertIn(key, first["details"])
        self.assertIs(type(first["valence"]), float)
        self.assertIs(type(first["activity"]), float)
        self.assertIs(type(first["confidence"]), float)
        self.assertIn(
            first["label"],
            {"neutral", "calm", "joy", "anger", "frustration", "fear", "sadness"},
        )
        self.assertEqual(first["action"], "ANSWER")


if __name__ == "__main__":
    unittest.main(verbosity=2)
