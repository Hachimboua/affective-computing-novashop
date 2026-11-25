"""Forty-message rehearsal using new English and Portuguese conversations."""
import csv
import math
from pathlib import Path
import unittest

from engine import config
from engine.engine import Engine


CONVERSATIONS = (
    (
        "english_delivery",
        (
            ("Hello, I need help checking a parcel's progress.", ("ANSWER",)),
            (
                "Could you help me locate the current status for order 583214?",
                ("ANSWER",),
            ),
            (
                "It was due Tuesday, but the parcel still has not arrived.",
                ("ANSWER_EMPATHIC", "OFFER_HUMAN"),
            ),
            (
                "The tracking page now shows the parcel at my local depot.",
                ("ANSWER", "ANSWER_EMPATHIC"),
            ),
            ("Thanks, that answered my question.", ("CLOSE_POSITIVE",)),
        ),
    ),
    (
        "english_product_and_return",
        (
            (
                "The Roam Mini speaker is a birthday gift, and I need product details.",
                ("ANSWER", "ASK_CLARIFICATION"),
            ),
            (
                "How does the speaker pair with a second Bluetooth device?",
                ("ANSWER",),
            ),
            (
                "The charging port on the speaker is cracked and will not work.",
                ("ANSWER_EMPATHIC", "OFFER_HUMAN"),
            ),
            (
                "I would like to send this device back and ask for a refund.",
                ("ANSWER", "ANSWER_EMPATHIC"),
            ),
            (
                "I really appreciate this; thank you, everything is now perfect.",
                ("CLOSE_POSITIVE",),
            ),
        ),
    ),
    (
        "english_handoff_and_legal",
        (
            ("Could you help me with a charge on my account?", ("ANSWER",)),
            (
                "The same billing amount appeared twice on my statement.",
                ("ANSWER", "ANSWER_EMPATHIC"),
            ),
            (
                "Please connect me with a real person to review it.",
                ("OFFER_HUMAN",),
            ),
            (
                "I already asked twice; if this is not corrected I will take it to court.",
                ("ESCALATE",),
            ),
            (
                "Thank you; I will wait for the person to explain the next steps.",
                ("CLOSE_POSITIVE", "ANSWER", "ANSWER_EMPATHIC"),
            ),
        ),
    ),
    (
        "portuguese_delivery",
        (
            ("Bom dia, preciso de ajuda com a minha encomenda.", ("ANSWER",)),
            (
                "Quero verificar o estado da encomenda 431762.",
                ("ANSWER",),
            ),
            (
                "A entrega está muito atrasada e continuo à espera.",
                ("ANSWER_EMPATHIC", "OFFER_HUMAN"),
            ),
            (
                "O artigo chegou partido e não consigo utilizá-lo.",
                ("ANSWER_EMPATHIC", "OFFER_HUMAN"),
            ),
            (
                "Obrigada, agora está tudo resolvido e a explicação foi excelente.",
                ("CLOSE_POSITIVE",),
            ),
        ),
    ),
    (
        "portuguese_support_intents",
        (
            (
                "O pagamento foi recusado apesar de o cartão estar válido.",
                ("ANSWER", "ANSWER_EMPATHIC"),
            ),
            (
                "Não consigo iniciar sessão na conta e preciso de recuperar o acesso.",
                ("ANSWER", "ANSWER_EMPATHIC", "ASK_CLARIFICATION"),
            ),
            (
                "Does the TrailPod speaker pair with two devices at once?",
                ("ANSWER", "ASK_CLARIFICATION"),
            ),
            (
                "Recebi um artigo errado, mas posso continuar a usar o carregador.",
                ("ANSWER", "ANSWER_EMPATHIC"),
            ),
            (
                "Muito obrigada; agora está tudo resolvido e fiquei contente com a ajuda.",
                ("CLOSE_POSITIVE",),
            ),
        ),
    ),
    (
        "english_sarcasm_and_negation",
        (
            (
                "I do not dislike the new headset, although its microphone has an irritating hiss.",
                ("ANSWER", "ANSWER_EMPATHIC"),
            ),
            (
                "The package is not missing; the tracking page says it is delayed.",
                ("ANSWER", "ANSWER_EMPATHIC"),
            ),
            (
                "Great, another delivery delay. Just what I needed.",
                ("ANSWER_EMPATHIC", "OFFER_HUMAN", "ESCALATE"),
            ),
            (
                "I am not unhappy with the replacement, but I am still waiting for the charger.",
                ("ANSWER", "ANSWER_EMPATHIC", "OFFER_HUMAN"),
            ),
            (
                "That is all for now; thanks for looking into it.",
                ("CLOSE_POSITIVE", "ANSWER_EMPATHIC"),
            ),
        ),
    ),
    (
        "short_and_unsupported",
        (
            ("Huh?", ("ASK_CLARIFICATION",)),
            ("No idea", ("ASK_CLARIFICATION", "OFFER_HUMAN")),
            (
                "Bitte prüfen Sie meine Bestellung.",
                ("ASK_CLARIFICATION", "OFFER_HUMAN"),
            ),
            (
                "Could you repeat that?",
                ("ANSWER", "ASK_CLARIFICATION", "OFFER_HUMAN"),
            ),
            ("?!?!", ("ASK_CLARIFICATION", "OFFER_HUMAN")),
        ),
    ),
    (
        "safety_and_resolution",
        (
            (
                "I am furious about the broken charger; it is useless.",
                ("ANSWER_EMPATHIC", "OFFER_HUMAN", "ESCALATE"),
            ),
            (
                "If this keeps happening, I might hurt myself.",
                ("ESCALATE",),
            ),
            (
                "I will contact consumer protection and file a formal claim over the duplicate fee.",
                ("ESCALATE",),
            ),
            (
                "I have decided to keep the headphones after all; the controls work well.",
                ("ANSWER", "ANSWER_EMPATHIC"),
            ),
            (
                "Thank you, that was excellent; everything is fixed and I am delighted.",
                ("CLOSE_POSITIVE",),
            ),
        ),
    ),
)


class RehearsalTests(unittest.TestCase):
    def test_new_conversations_meet_the_action_target(self):
        messages = [
            text
            for _, conversation in CONVERSATIONS
            for text, _ in conversation
        ]
        self.assertEqual(len(messages), 40)
        self.assertEqual(len(set(messages)), 40)

        data_path = (
            Path(__file__).resolve().parent.parent
            / "engine"
            / "evaluation"
            / "data"
            / "messages.csv"
        )
        with data_path.open("r", encoding="utf-8", newline="") as stream:
            evaluation_texts = {row["text"] for row in csv.DictReader(stream)}
        self.assertFalse(
            evaluation_texts.intersection(messages),
            "Rehearsal messages must be absent from messages.csv.",
        )
        other_test_sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in Path(__file__).resolve().parent.glob("*.py")
            if path.resolve() != Path(__file__).resolve()
        )
        self.assertFalse(
            any(message in other_test_sources for message in messages),
            "Rehearsal messages must be new to the test suite.",
        )

        passed = 0
        observed_actions = set()
        for conversation_name, conversation in CONVERSATIONS:
            engine = Engine()
            previous_reply = None
            for turn, (text, acceptable_actions) in enumerate(conversation, 1):
                with self.subTest(
                    conversation=conversation_name,
                    turn=turn,
                    text=text,
                ):
                    result = engine.process(text)
                    observed_actions.add(result["action"])
                    if result["action"] in acceptable_actions:
                        passed += 1
                    self.assertNotEqual(result["reply"], previous_reply)
                    previous_reply = result["reply"]

        minimum_passes = math.ceil(
            len(messages) * config.HIDDEN_REHEARSAL_MIN_PASS_RATE
        )
        self.assertGreaterEqual(
            passed,
            minimum_passes,
            "rehearsal pass rate: %d/%d" % (passed, len(messages)),
        )
        self.assertEqual(
            observed_actions,
            {
                "ANSWER",
                "ANSWER_EMPATHIC",
                "ASK_CLARIFICATION",
                "OFFER_HUMAN",
                "ESCALATE",
                "CLOSE_POSITIVE",
            },
        )


if __name__ == "__main__":
    unittest.main()
