"""Action ordering, language-appropriate replies, and conversation policy tests."""
import csv
from pathlib import Path
import unittest

from engine import config
from engine.engine import Engine


class PolicyTests(unittest.TestCase):
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
        self.assertFalse(evaluation_texts.intersection(sentences))

    def test_thirty_message_action_rehearsal(self):
        examples = (
            ("I might hurt myself tonight; I need help.", "ESCALATE"),
            ("Could you connect me to a real person?", "OFFER_HUMAN"),
            ("I am taking this invoice issue to court.", "ESCALATE"),
            ("That's all I needed, thanks for your help!", "CLOSE_POSITIVE"),
            ("What is the warranty period for this portable speaker?", "ANSWER"),
            ("I'm exhausted by this broken charger.", "ANSWER_EMPATHIC"),
            ("I cannot follow the instructions so far.", "ASK_CLARIFICATION"),
            ("Quero fazer mal a mim pr\u00f3prio e preciso de ajuda.", "ESCALATE"),
            ("Quero falar com um agente humano.", "OFFER_HUMAN"),
            ("Vou levar esta cobran\u00e7a ao tribunal.", "ESCALATE"),
            ("Obrigado, ficou tudo resolvido!", "CLOSE_POSITIVE"),
            ("Qual \u00e9 o prazo de garantia do carregador?", "ANSWER"),
            ("Estou cansado e triste com a encomenda perdida.", "ANSWER_EMPATHIC"),
            ("Could you make that clearer for me?", "ASK_CLARIFICATION"),
            ("Is this keyboard compatible with Linux?", "ANSWER"),
            ("I'm disappointed that the replacement arrived damaged.", "ANSWER_EMPATHIC"),
            ("Whatever.", "ASK_CLARIFICATION"),
            ("What warranty options are available for this camera?", "ANSWER"),
            ("The order is still missing, and I'm getting frustrated.", "ANSWER_EMPATHIC"),
            ("I want to speak to a person about my order.", "OFFER_HUMAN"),
            ("I can take this to the consumer protection office.", "ESCALATE"),
            ("Please consider my support request finished, thank you.", "CLOSE_POSITIVE"),
            ("Preciso de saber se o teclado \u00e9 compat\u00edvel com este computador.", "ANSWER"),
            ("A entrega est\u00e1 atrasada e estou dececionado.", "ANSWER_EMPATHIC"),
            ("I need a bit more context.", "ASK_CLARIFICATION"),
            ("The broken screen has left me really upset.", "ANSWER_EMPATHIC"),
            ("I am unsure what to do next.", "ASK_CLARIFICATION"),
            ("Please explain the warranty coverage for this monitor.", "ANSWER"),
            ("Est\u00e1 tudo resolvido, obrigada pela ajuda!", "CLOSE_POSITIVE"),
            ("Vou apresentar uma reclama\u00e7\u00e3o formal sobre esta conta.", "ESCALATE"),
        )
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
            evaluation_texts.intersection(text for text, _ in examples)
        )
        passed = sum(
            Engine().process(text)["action"] == expected
            for text, expected in examples
        )
        self.assertEqual(passed, 30, "rehearsal pass count: %d/30" % passed)

    def test_each_action_is_reachable(self):
        examples = (
            ("I might hurt myself tonight; please help.", "ESCALATE"),
            ("Please connect me with a real person.", "OFFER_HUMAN"),
            ("I will contact the court about this.", "ESCALATE"),
            ("Thanks, that completely solved my question!", "CLOSE_POSITIVE"),
            ("?", "ASK_CLARIFICATION"),
            ("I'm exhausted and disappointed about this delay.", "ANSWER_EMPATHIC"),
            ("What is the warranty coverage for the blender?", "ANSWER"),
        )
        observed = set()
        for text, expected in examples:
            with self.subTest(expected=expected, text=text):
                result = Engine().process(text)
                self.assertEqual(result["action"], expected)
                self.assertIn("rule", result["details"])
                self.assertIn("reason", result["details"])
                observed.add(result["action"])
        self.assertEqual(
            observed,
            {
                "ANSWER",
                "ANSWER_EMPATHIC",
                "ASK_CLARIFICATION",
                "OFFER_HUMAN",
                "ESCALATE",
                "CLOSE_POSITIVE",
            },
        )

    def test_plain_neutral_questions_get_neutral_confidence_and_answer(self):
        examples = (
            ("Do you ship to the Azores?", "en"),
            ("Can I pay with PayPal?", "en"),
            ("What time do you close on Sundays?", "en"),
            ("Posso pagar com MB Way?", "pt"),
            ("Têm loja física no Porto?", "pt"),
        )
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
            evaluation_texts.intersection(text for text, _ in examples)
        )

        for text, expected_language in examples:
            with self.subTest(text=text):
                result = Engine().process(text)
                self.assertEqual(result["details"]["lang"], expected_language)
                self.assertEqual(result["details"]["intent"], "UNKNOWN")
                self.assertEqual(result["action"], "ANSWER")
                self.assertEqual(result["label"], "neutral")
                self.assertIn("no_affect_words", result["flags"])
                self.assertNotIn("unsupported_language", result["flags"])
                self.assertAlmostEqual(
                    result["confidence"],
                    config.NEUTRAL_CONFIDENCE
                    * result["details"]["lang_confidence"],
                )
                invitation = (
                    "número da encomenda"
                    if expected_language == "pt"
                    else "order number"
                )
                self.assertIn(invitation, result["reply"].casefold())

        boundary_question = "Where is it?"
        self.assertNotIn(boundary_question, evaluation_texts)
        boundary_result = Engine().process(boundary_question)
        self.assertEqual(boundary_result["details"]["lang"], "en")
        self.assertEqual(boundary_result["details"]["intent"], "UNKNOWN")
        self.assertIn("no_affect_words", boundary_result["flags"])
        self.assertAlmostEqual(
            boundary_result["confidence"],
            config.NEUTRAL_CONFIDENCE
            * boundary_result["details"]["lang_confidence"],
        )

    def test_short_latin_messages_request_clarification_not_language(self):
        examples = ("meh", "eh", "??", "uhh", "k", "je suis", "ich bin")
        self.assert_new_sentences(examples)
        for text in examples:
            with self.subTest(text=text):
                result = Engine().process(text)
                self.assertEqual(result["action"], "ASK_CLARIFICATION")
                self.assertIn("short_message", result["flags"])
                self.assertNotIn("unsupported_language", result["flags"])
                self.assertNotIn(
                    "Please write in one of those languages.", result["reply"]
                )

    def test_short_shout_in_negative_context_offers_human(self):
        conversation = (
            "Hello, I'm checking on my tablet order.",
            "It's now a week late.",
            "This is getting really annoying, nobody tells me anything.",
            "I'm absolutely furious, this is the worst service ever!!!",
            "UNBELIEVABLE. STILL NOTHING!!!",
        )
        self.assert_new_sentences(conversation)
        engine = Engine()
        for text in conversation[:-1]:
            engine.process(text)
        result = engine.process(conversation[-1])
        self.assertIn(result["action"], ("OFFER_HUMAN", "ESCALATE"))
        self.assertEqual(result["details"]["lang"], "en")
        self.assertNotIn("unsupported_language", result["flags"])

    def test_explicit_legal_cue_overrides_positive_closing_language(self):
        result = Engine().process(
            "Thanks for helping, but I will contact a lawyer if this remains unresolved."
        )
        self.assertEqual(result["action"], "ESCALATE")
        self.assertEqual(result["details"]["rule"], "R2_ESCALATE")

    def test_sarcasm_never_closes_positive(self):
        result = Engine().process("Thanks for nothing.")
        self.assertNotEqual(result["action"], "CLOSE_POSITIVE")

    def test_clarification_loop_is_capped(self):
        engine = Engine()
        first = engine.process("ok")
        second = engine.process("?")
        third = engine.process("hmm")
        self.assertEqual(first["action"], "ASK_CLARIFICATION")
        self.assertEqual(second["action"], "ASK_CLARIFICATION")
        self.assertEqual(third["action"], "OFFER_HUMAN")
        self.assertEqual(third["details"]["rule"], "R4_UNCERTAIN")
        self.assertEqual(first["details"]["state"]["clar_streak"], 1)
        self.assertEqual(second["details"]["state"]["clar_streak"], 2)

    def test_human_offer_is_not_repeated_immediately(self):
        engine = Engine()
        first = engine.process("This delay is frustrating and still unresolved.")
        second = engine.process("This delay is frustrating and still unresolved.")
        third = engine.process("This delay is frustrating and still unresolved.")
        self.assertEqual(first["action"], "ANSWER_EMPATHIC")
        self.assertEqual(second["action"], "OFFER_HUMAN")
        self.assertEqual(third["action"], "ANSWER_EMPATHIC")
        self.assertEqual(third["details"]["rule"], "R5_OFFER_HUMAN")

    def test_declined_handoff_is_not_reoffered_or_escalated(self):
        engine = Engine()
        offered = engine.process("Please connect me with a real person.")
        declined = engine.process("No thanks, I don't want a person.")
        self.assertEqual(offered["action"], "OFFER_HUMAN")
        self.assertNotIn(
            declined["action"], ("OFFER_HUMAN", "ESCALATE", "CLOSE_POSITIVE")
        )

    def test_portuguese_and_unsupported_replies(self):
        portuguese = Engine().process("Estou cansado de repetir o mesmo pedido.")
        self.assertEqual(portuguese["details"]["lang"], "pt")
        self.assertIn("Lamento", portuguese["reply"])
        unsupported = Engine().process("Здравствуйте")
        self.assertIn("unsupported_language", unsupported["flags"])
        self.assertIn("English or Portuguese", unsupported["reply"])
        self.assertIn("português", unsupported["reply"])

    def test_reply_uses_product_without_repeating_the_generic_item(self):
        result = Engine().process("My laptop arrived broken.")
        self.assertIn("your laptop", result["reply"])
        self.assertNotIn("this item for your laptop", result["reply"])

    def test_reply_variants_are_deterministic(self):
        engine = Engine()
        first = engine.process("What is the warranty coverage?")
        second = engine.process("What is the warranty coverage?")
        engine.reset()
        reset_first = engine.process("What is the warranty coverage?")
        self.assertEqual(first["reply"], reset_first["reply"])
        self.assertNotEqual(first["reply"], second["reply"])

    def test_reset_matches_a_fresh_engine(self):
        engine = Engine()
        engine.process("The headphones arrived with a cracked case.")
        engine.process("I am still disappointed about the damage.")
        engine.reset()
        reset_result = engine.process(
            "I feel disappointed that the headset arrived with a cracked case."
        )
        fresh_result = Engine().process(
            "I feel disappointed that the headset arrived with a cracked case."
        )
        self.assertEqual(reset_result, fresh_result)


if __name__ == "__main__":
    unittest.main()
