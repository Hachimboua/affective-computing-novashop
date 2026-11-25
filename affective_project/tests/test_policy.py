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
        results = [
            Engine().process(text)
            for text, _ in examples
        ]
        passed = sum(
            result["action"] == expected
            for result, (_, expected) in zip(results, examples)
        )
        self.assertEqual(passed, 30, "rehearsal pass count: %d/30" % passed)
        closing_phrases = (
            "glad i could help",
            "glad we could resolve",
            "happy i could help",
            "thank you for contacting novashop",
            "have a good day",
            "ainda bem que conseguimos resolver",
            "fico contente por ter ajudado",
            "obrigado por contactar a novashop",
            "tenha um bom dia",
            "ainda bem que pude ajudar",
        )
        for result in results:
            if result["action"] in ("ANSWER_EMPATHIC", "OFFER_HUMAN", "ESCALATE"):
                with self.subTest(action=result["action"]):
                    for phrase in closing_phrases:
                        self.assertNotIn(phrase, result["reply"].casefold())

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

    def test_only_safety_escalations_mention_emergency_services(self):
        safety_examples = (
            (
                "I might hurt myself tonight; I need help.",
                "en",
                "emergency services",
            ),
            (
                "Quero fazer mal a mim próprio e preciso de ajuda.",
                "pt",
                "serviços de emergência locais",
            ),
        )
        non_safety_examples = (
            ("I am taking this invoice issue to court.", "en"),
            ("Vou levar esta cobrança ao tribunal.", "pt"),
            ("I will hurt you if you ignore me.", "en"),
        )
        anger_sequences = (
            (
                "I am furious about this disgraceful failure!!!",
                "This is outrageous, I am absolutely enraged!!!",
            ),
            (
                "Estou furioso com esta falha e indignado!!!",
                "Estou revoltado e muito zangado com o problema!!!",
            ),
        )
        all_messages = [
            text for text, _, _ in safety_examples
        ] + [text for text, _ in non_safety_examples]
        all_messages.extend(text for sequence in anger_sequences for text in sequence)
        self.assert_new_sentences(all_messages)

        for text, language, emergency_phrase in safety_examples:
            with self.subTest(safety=True, language=language):
                result = Engine().process(text)
                self.assertEqual(result["action"], "ESCALATE")
                self.assertEqual(result["details"]["lang"], language)
                self.assertIn("safety", result["flags"])
                self.assertIn(emergency_phrase, result["reply"].casefold())

        non_safety_results = []
        for text, language in non_safety_examples:
            with self.subTest(safety=False, language=language):
                result = Engine().process(text)
                self.assertEqual(result["action"], "ESCALATE")
                self.assertEqual(result["details"]["lang"], language)
                self.assertNotIn("safety", result["flags"])
                non_safety_results.append(result)

        for sequence in anger_sequences:
            engine = Engine()
            engine.process(sequence[0])
            result = engine.process(sequence[1])
            self.assertEqual(result["action"], "ESCALATE")
            self.assertNotIn("safety", result["flags"])
            non_safety_results.append(result)

        for result in non_safety_results:
            with self.subTest(language=result["details"]["lang"]):
                person_word = (
                    "person"
                    if result["details"]["lang"] == "en"
                    else "pessoa"
                )
                self.assertIn(person_word, result["reply"].casefold())
                self.assertNotIn("emergency services", result["reply"].casefold())
                self.assertNotIn("serviços de emergência", result["reply"].casefold())
                self.assertNotIn("immediate danger", result["reply"].casefold())
                self.assertNotIn("perigo imediato", result["reply"].casefold())

    def test_explicit_legal_cue_overrides_positive_closing_language(self):
        result = Engine().process(
            "Thanks for helping, but I will contact a lawyer if this remains unresolved."
        )
        self.assertEqual(result["action"], "ESCALATE")
        self.assertEqual(result["details"]["rule"], "R2_ESCALATE")

    def test_sarcasm_never_closes_positive(self):
        result = Engine().process("Thanks for nothing.")
        self.assertNotEqual(result["action"], "CLOSE_POSITIVE")
        self.assertNotIn("glad i could help", result["reply"].casefold())

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

    def test_supported_intents_get_specific_safe_next_steps(self):
        examples = (
            (
                "en",
                "Could you help me locate the current status for my order?",
                "ORDER_STATUS",
                ("order number", "tracking update"),
            ),
            (
                "pt",
                "Pode ajudar-me a verificar o estado do pedido?",
                "ORDER_STATUS",
                ("número da encomenda", "rastreio"),
            ),
            (
                "en",
                "My parcel is delayed, and the tracking page has not changed.",
                "DELIVERY_DELAY",
                ("order number", "tracking update"),
            ),
            (
                "pt",
                "A minha encomenda continua atrasada.",
                "DELIVERY_DELAY",
                ("número da encomenda", "rastreio"),
            ),
            (
                "en",
                "The display on my phone is cracked and unusable.",
                "DAMAGED_OR_DEFECTIVE",
                ("describe the issue", "order number"),
            ),
            (
                "pt",
                "O ecrã do meu telemóvel está partido.",
                "DAMAGED_OR_DEFECTIVE",
                ("descreva o problema", "número da encomenda"),
            ),
            (
                "en",
                "The box contains the wrong item, not the headphones I ordered.",
                "WRONG_ITEM",
                ("what you ordered", "order number"),
            ),
            (
                "pt",
                "Recebi um produto errado, não o carregador que pedi.",
                "WRONG_ITEM",
                ("o que pediu", "número da encomenda"),
            ),
            (
                "en",
                "I need to return this item and ask about a refund.",
                "REFUND_RETURN",
                ("return or refund", "order number"),
            ),
            (
                "pt",
                "Quero pedir um reembolso e saber como iniciar a devolução.",
                "REFUND_RETURN",
                ("reembolso", "número da encomenda"),
            ),
            (
                "en",
                "A card payment appears twice on my statement.",
                "PAYMENT_BILLING",
                ("order number", "without sending card details"),
            ),
            (
                "pt",
                "Estou com um problema: o pagamento do meu cartão foi duplicado.",
                "PAYMENT_BILLING",
                ("número da encomenda", "sem enviar dados do cartão"),
            ),
            (
                "en",
                "My account locked after I entered the wrong password.",
                "ACCOUNT_LOGIN",
                ("sign-in error", "password"),
            ),
            (
                "pt",
                "A minha conta está bloqueada e não consigo iniciar sessão.",
                "ACCOUNT_LOGIN",
                ("erro de acesso", "palavra-passe"),
            ),
            (
                "en",
                "How does this travel speaker connect to Bluetooth?",
                "PRODUCT_QUESTION",
                ("product model", "feature"),
            ),
            (
                "pt",
                "Este carregador é compatível com tomadas USB-C?",
                "PRODUCT_QUESTION",
                ("modelo do produto", "característica"),
            ),
        )
        self.assert_new_sentences(text for _, text, _, _ in examples)
        unsupported_claims = (
            "your order is on its way",
            "will arrive tomorrow",
            "your refund has been approved",
            "a encomenda já foi enviada",
            "chegará amanhã",
            "o reembolso foi aprovado",
        )
        for language, text, expected_intent, next_steps in examples:
            with self.subTest(language=language, intent=expected_intent):
                result = Engine().process(text)
                self.assertEqual(result["details"]["lang"], language)
                self.assertEqual(result["details"]["intent"], expected_intent)
                reply = result["reply"].casefold()
                for phrase in next_steps:
                    self.assertIn(phrase.casefold(), reply)
                for claim in unsupported_claims:
                    self.assertNotIn(claim, reply)

    def test_repeated_intent_replies_do_not_repeat_consecutive_steps(self):
        engine = Engine()
        replies = [
            engine.process(
                "How does the portable speaker pair with Bluetooth?"
            )["reply"]
            for _ in range(4)
        ]
        for previous, current in zip(replies, replies[1:]):
            self.assertNotEqual(previous, current)

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
        reset_comparable = dict(reset_result)
        fresh_comparable = dict(fresh_result)
        reset_comparable["details"] = dict(reset_result["details"])
        fresh_comparable["details"] = dict(fresh_result["details"])
        reset_comparable["details"].pop("timing_ms")
        fresh_comparable["details"].pop("timing_ms")
        self.assertEqual(reset_comparable, fresh_comparable)


if __name__ == "__main__":
    unittest.main()
