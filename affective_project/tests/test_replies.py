"""Reply consistency regressions: the reply must agree with the chosen action.

All sentences here are new and are not part of the evaluation messages.
Run with:  python -m unittest tests.test_replies
"""
import csv
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from harness.loader import load_engine  # noqa: E402

GENERIC_SENTENCES = (
    "i can help with a novashop question",
    "posso ajudar com uma questão da novashop",
)
CLARIFICATION_WORDS = ("a little more", "more detail", "um pouco mais")


def _evaluation_texts():
    path = os.path.join(ROOT, "engine", "evaluation", "data", "messages.csv")
    with open(path, encoding="utf-8", newline="") as handle:
        return {row["text"].strip().casefold() for row in csv.DictReader(handle)}


class ReplyConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.engine = load_engine(ROOT)
        self.engine.reset()
        self.evaluation_texts = _evaluation_texts()

    def _run(self, messages):
        self.engine.reset()
        results = []
        for text in messages:
            self.assertNotIn(text.strip().casefold(), self.evaluation_texts, text)
            results.append(self.engine.process(text))
        return results

    def test_clarification_cap_reply_offers_a_person(self):
        results = self._run(["eh", "uhh", "hmm k"])
        last = results[-1]
        self.assertEqual(last["action"], "OFFER_HUMAN")
        reply = last["reply"].casefold()
        self.assertTrue("person" in reply or "pessoa" in reply, last["reply"])
        for words in CLARIFICATION_WORDS:
            self.assertNotIn(words, reply)

    def test_unsupported_language_escalation_is_not_a_language_request(self):
        result = self._run(["Ich werde meinen Anwalt einschalten, lawyer!"])[0]
        if result["action"] == "ESCALATE":
            self.assertNotIn("please write in", result["reply"].casefold())

    def test_portuguese_payment_worry_gets_payment_reply(self):
        result = self._run(["Estou aflita, acho que paguei a mesma fatura duas vezes."])[0]
        self.assertEqual(result["details"]["intent"], "PAYMENT_BILLING")
        reply = result["reply"].casefold()
        self.assertTrue("cobrança" in reply or "cartão" in reply or "faturação" in reply, result["reply"])

    def test_portuguese_charged_twice_detected(self):
        result = self._run(["Foi-me cobrado o portátil duas vezes no cartão."])[0]
        self.assertEqual(result["details"]["intent"], "PAYMENT_BILLING")

    def test_follow_up_uses_earlier_problem(self):
        results = self._run([
            "My order 55123 is two weeks late.",
            "Nobody tells me anything, this is so annoying.",
        ])
        follow_up = results[-1]
        self.assertEqual(follow_up["details"].get("context_intent"), "DELIVERY_DELAY")
        reply = follow_up["reply"].casefold()
        self.assertTrue("tracking" in reply or "delivery" in reply or "delay" in reply, follow_up["reply"])

    def test_no_generic_sentence_in_negative_conversations(self):
        conversations = [
            ["Hello there.", "This is getting so irritating, nobody replies.", "Honestly, what a mess."],
            ["Olá.", "Isto é mesmo irritante, ninguém responde.", "Que confusão, a sério."],
            ["My speaker arrived with a crack.", "I'm fed up, honestly.", "Whatever, I'm tired of this."],
        ]
        for messages in conversations:
            for result in self._run(messages):
                reply = result["reply"].casefold()
                for sentence in GENERIC_SENTENCES:
                    self.assertNotIn(sentence, reply, (messages, result["reply"]))

    def test_reply_matches_action_family(self):
        conversations = [
            ["I want to speak to a human right now."],
            ["Please connect me with a person."],
            ["Quero falar com um assistente humano, por favor."],
            ["I'll be contacting my lawyer about this order."],
            ["Lovely, it's sorted now, thank you and bye!"],
        ]
        for messages in conversations:
            result = self._run(messages)[-1]
            reply = result["reply"].casefold()
            if result["action"] in ("OFFER_HUMAN", "ESCALATE"):
                self.assertTrue("person" in reply or "pessoa" in reply or "human" in reply, result["reply"])
                self.assertNotIn("glad", reply)
            if result["action"] == "CLOSE_POSITIVE":
                self.assertNotIn("person", reply)


if __name__ == "__main__":
    unittest.main(verbosity=2)
