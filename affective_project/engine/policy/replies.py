"""Short deterministic replies that avoid claims about live order systems."""

_EN_STEPS = {
    "HUMAN_REQUEST": "I can offer a handoff to a human support agent.",
    "DELIVERY_DELAY": "I can help check the delivery details{subject}.",
    "DAMAGED_OR_DEFECTIVE": "I can help review the options{subject}.",
    "WRONG_ITEM": "I can help review the options for the item you received.",
    "REFUND_RETURN": "I can explain the return steps and how to start a request.",
    "PAYMENT_BILLING": "I can help review the payment details with you.",
    "ACCOUNT_LOGIN": "I can guide you through account access steps.",
    "PRODUCT_QUESTION": "I can help explain the product information.",
    "ORDER_STATUS": "I can help check the order details{subject}.",
    "CLOSING_THANKS": "I'm glad I could help.",
    "GREETING": "I can help with a NovaShop question.",
    "COMPLAINT_GENERAL": "I can help identify a practical next step.",
    "UNKNOWN": "I can help with a NovaShop question.",
}
_PT_STEPS = {
    "HUMAN_REQUEST": "Posso oferecer o encaminhamento para um agente humano.",
    "DELIVERY_DELAY": "Posso ajudar a verificar os detalhes da entrega{subject}.",
    "DAMAGED_OR_DEFECTIVE": "Posso ajudar a rever as opções{subject}.",
    "WRONG_ITEM": "Posso ajudar a rever as opções para o artigo recebido.",
    "REFUND_RETURN": "Posso explicar os passos da devolução e como iniciar um pedido.",
    "PAYMENT_BILLING": "Posso ajudar a analisar os detalhes do pagamento.",
    "ACCOUNT_LOGIN": "Posso orientar os passos para aceder à conta.",
    "PRODUCT_QUESTION": "Posso ajudar a explicar as informações do produto.",
    "ORDER_STATUS": "Posso ajudar a verificar os detalhes da encomenda{subject}.",
    "CLOSING_THANKS": "Ainda bem que pude ajudar.",
    "GREETING": "Posso ajudar com uma questão da NovaShop.",
    "COMPLAINT_GENERAL": "Posso ajudar a identificar um próximo passo prático.",
    "UNKNOWN": "Posso ajudar com uma questão da NovaShop.",
}
_EN_PROBLEMS = {
    "DELIVERY_DELAY": "the delivery issue",
    "DAMAGED_OR_DEFECTIVE": "the problem with the item",
    "WRONG_ITEM": "the item mix-up",
    "REFUND_RETURN": "the return or refund question",
    "PAYMENT_BILLING": "the payment question",
    "ACCOUNT_LOGIN": "the account access problem",
    "PRODUCT_QUESTION": "the product question",
    "ORDER_STATUS": "the order question",
    "COMPLAINT_GENERAL": "the problem you described",
    "UNKNOWN": "this issue",
}
_PT_PROBLEMS = {
    "DELIVERY_DELAY": "o problema com a entrega",
    "DAMAGED_OR_DEFECTIVE": "o problema com o artigo",
    "WRONG_ITEM": "a troca de artigo",
    "REFUND_RETURN": "a questão da devolução ou reembolso",
    "PAYMENT_BILLING": "a questão do pagamento",
    "ACCOUNT_LOGIN": "o problema de acesso à conta",
    "PRODUCT_QUESTION": "a questão sobre o produto",
    "ORDER_STATUS": "a questão sobre a encomenda",
    "COMPLAINT_GENERAL": "o problema que descreveu",
    "UNKNOWN": "esta questão",
}

_EN_ACTION_PATTERNS = {
    "ANSWER": (
        "{step}",
        "I can help with that. {step}",
    ),
    "ANSWER_EMPATHIC": (
        "I'm sorry about {problem}. {step}",
        "I'm sorry you're dealing with {problem}. {step}",
    ),
    "ASK_CLARIFICATION": (
        "Could you share a little more about {problem}?",
        "What would you like me to help with regarding {problem}?",
    ),
    "OFFER_HUMAN": (
        "I'm an automated assistant. I can offer a human handoff for {problem}.",
        "I'm an automated assistant. Would you like me to request a human handoff for {problem}?",
    ),
    "ESCALATE": (
        "I'm an automated assistant. This needs urgent attention from a person.",
        "I'm an automated assistant. A person should review this urgently.",
    ),
    "CLOSE_POSITIVE": (
        "I'm glad we could resolve this. Thank you for contacting NovaShop.",
        "I'm happy I could help. Have a good day.",
    ),
}
_PT_ACTION_PATTERNS = {
    "ANSWER": (
        "{step}",
        "Posso ajudar com isso. {step}",
    ),
    "ANSWER_EMPATHIC": (
        "Lamento {problem}. {step}",
        "Lamento que esteja a lidar com {problem}. {step}",
    ),
    "ASK_CLARIFICATION": (
        "Pode explicar um pouco melhor {problem}?",
        "Em que gostaria que ajudasse relativamente a {problem}?",
    ),
    "OFFER_HUMAN": (
        "Sou um assistente automatizado. Posso oferecer o encaminhamento para uma pessoa sobre {problem}.",
        "Sou um assistente automatizado. Gostaria que pedisse o apoio de uma pessoa para {problem}?",
    ),
    "ESCALATE": (
        "Sou um assistente automatizado. Esta situação precisa de atenção urgente de uma pessoa.",
        "Sou um assistente automatizado. Uma pessoa deve analisar isto com urgência.",
    ),
    "CLOSE_POSITIVE": (
        "Ainda bem que conseguimos resolver a questão. Obrigado por contactar a NovaShop.",
        "Fico contente por ter ajudado. Tenha um bom dia.",
    ),
}


def _subject(entities, language, intent):
    order_number = entities.get("order_number")
    if order_number:
        if language == "pt":
            return " para a encomenda %s" % order_number
        return " for order %s" % order_number
    product = entities.get("product")
    if product and intent != "ORDER_STATUS":
        if language == "pt":
            return " para o produto %s" % product
        return " for your %s" % product
    if intent == "DAMAGED_OR_DEFECTIVE":
        return " para este artigo" if language == "pt" else " for this item"
    return ""


def _problem(intent, entities, language):
    order_number = entities.get("order_number")
    if order_number:
        if language == "pt":
            return "a encomenda %s" % order_number
        return "order %s" % order_number
    product = entities.get("product")
    if product:
        if language == "pt":
            return "o problema com o produto %s" % product
        return "the problem with your %s" % product
    problems = _PT_PROBLEMS if language == "pt" else _EN_PROBLEMS
    return problems.get(intent, problems["UNKNOWN"])


def _variant(templates, turn_index):
    return templates[(max(1, int(turn_index)) - 1) % len(templates)]


def render_reply(action, intent, language, turn_index, entities=None, flags=None):
    """Render a two-variant reply in a supported language or bilingually."""
    entities = entities or {}
    flags = set(flags or ())
    if (
        "unsupported_language" not in flags
        and language not in ("en", "pt")
        and "short_message" in flags
    ):
        return _variant(
            (
                "Could you tell me a little more so I can help? / "
                "Pode dizer-me um pouco mais para eu poder ajudar?",
                "Please share a little more detail. / "
                "Partilhe um pouco mais de informação, por favor.",
            ),
            turn_index,
        )
    if "unsupported_language" in flags or language not in ("en", "pt"):
        return (
            "Sorry, I can understand English or Portuguese. Please write in one "
            "of those languages. I'm an automated assistant and can offer a "
            "human handoff. / Desculpe, só consigo compreender inglês ou "
            "português. Escreva numa dessas línguas. Sou um assistente "
            "automatizado e posso oferecer o apoio de uma pessoa."
        )

    subject = _subject(entities, language, intent)
    if "safety" in flags and action == "ESCALATE":
        if language == "pt":
            return _variant(
                (
                    "Sou um assistente automatizado. Se alguém estiver em "
                    "perigo imediato, contacte os serviços de emergência "
                    "locais e uma pessoa de confiança.",
                    "Esta situação precisa de apoio humano imediato. Se houver "
                    "perigo agora, contacte os serviços de emergência locais "
                    "e alguém em quem confie.",
                ),
                turn_index,
            )
        return _variant(
            (
                "I'm an automated assistant. If anyone is in immediate danger, "
                "contact local emergency services and someone you trust.",
                "This needs immediate human support. If there is danger now, "
                "contact local emergency services and a trusted person.",
            ),
            turn_index,
        )

    if language == "pt":
        step = _PT_STEPS.get(intent, _PT_STEPS["UNKNOWN"]).format(
            subject=subject
        )
        if intent == "UNKNOWN" and "no_affect_words" in flags:
            step = (
                "Diga-me um pouco mais sobre a sua questão. Se for sobre uma "
                "encomenda, indique o número da encomenda."
            )
        problem = _problem(intent, entities, language)
        pattern = _variant(_PT_ACTION_PATTERNS[action], turn_index)
    else:
        step = _EN_STEPS.get(intent, _EN_STEPS["UNKNOWN"]).format(
            subject=subject
        )
        if intent == "UNKNOWN" and "no_affect_words" in flags:
            step = (
                "Tell me a little more about your question. If it concerns an "
                "order, please include the order number."
            )
        problem = _problem(intent, entities, language)
        pattern = _variant(_EN_ACTION_PATTERNS[action], turn_index)
    return pattern.format(step=step, problem=problem)
