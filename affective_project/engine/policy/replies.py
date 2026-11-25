"""Short deterministic replies that avoid claims about live order systems."""

_EN_STEPS = {
    "HUMAN_REQUEST": (
        "I can offer a handoff to a human support agent.",
        "I can ask the support team to connect you with a person.",
    ),
    "DELIVERY_DELAY": (
        "Please share your order number and latest tracking update so I can help review the delay.",
        "Tell me your order number and what the tracking page currently shows, and I can help review the delay.",
    ),
    "DAMAGED_OR_DEFECTIVE": (
        "Please describe the issue{subject} and share the order number so I can outline the next support steps.",
        "Tell me what is wrong{subject} and include your order number so I can explain the available support options.",
    ),
    "WRONG_ITEM": (
        "Please share your order number and tell me what you ordered and what arrived so support can review the next step.",
        "Tell me what you expected and what arrived, with the order number, so support can review the mismatch.",
    ),
    "REFUND_RETURN": (
        "Tell me whether you want a return or refund, and share your order number so I can explain the next steps.",
        "Share your order number and say whether you are asking about a return or refund so I can outline the process.",
    ),
    "PAYMENT_BILLING": (
        "Please share your order number and describe the charge without sending card details so I can help review it.",
        "Describe the billing issue and include the order number if available; do not send card details.",
    ),
    "ACCOUNT_LOGIN": (
        "Share the sign-in error, not your password or verification code, so I can guide the account-recovery step.",
        "Tell me what happens when you try to sign in; please do not share passwords or verification codes.",
    ),
    "PRODUCT_QUESTION": (
        "Share the product model and the feature or specification you want to check.",
        "Tell me the product model and what feature you would like to know about.",
    ),
    "ORDER_STATUS": (
        "Please share your order number and latest tracking update so I can help review the order status.",
        "Send the order number and most recent tracking update, and I can help interpret the status.",
    ),
    "CLOSING_THANKS": (
        "I can continue to help if something is still unresolved.",
        "If another question comes up, tell me what you need and I can help with the next step.",
    ),
    "GREETING": (
        "Tell me what you would like help with, and I will guide you to the next step.",
        "Share your question and I will help identify a useful next step.",
    ),
    "COMPLAINT_GENERAL": (
        "Please describe what happened and include the order number if it concerns an order.",
        "Tell me what went wrong; if it is about an order, include its order number.",
    ),
    "UNKNOWN": (
        "I can help with a NovaShop question.",
        "Tell me what you would like to know, and I can suggest a next step.",
    ),
}
_PT_STEPS = {
    "HUMAN_REQUEST": (
        "Posso encaminhar o pedido para um agente de apoio humano.",
        "Posso pedir à equipa de apoio que o contacte através de uma pessoa.",
    ),
    "DELIVERY_DELAY": (
        "Indique o número da encomenda e a atualização mais recente do rastreio para eu ajudar a analisar o atraso.",
        "Diga-me o número da encomenda e o que aparece no rastreio para eu ajudar a analisar o atraso.",
    ),
    "DAMAGED_OR_DEFECTIVE": (
        "Descreva o problema{subject} e indique o número da encomenda para eu explicar os próximos passos de apoio.",
        "Diga o que está danificado{subject} e inclua o número da encomenda para eu explicar as opções de apoio.",
    ),
    "WRONG_ITEM": (
        "Indique o número da encomenda e diga o que pediu e o que recebeu para a equipa poder analisar o próximo passo.",
        "Descreva o artigo esperado e o recebido, com o número da encomenda, para a equipa poder analisar a troca.",
    ),
    "REFUND_RETURN": (
        "Diga se pretende devolver o artigo ou pedir um reembolso e indique o número da encomenda para eu explicar os próximos passos.",
        "Partilhe o número da encomenda e indique se pretende uma devolução ou um reembolso para eu explicar o processo.",
    ),
    "PAYMENT_BILLING": (
        "Indique o número da encomenda e descreva a cobrança sem enviar dados do cartão para eu ajudar a analisá-la.",
        "Descreva o problema de faturação e indique o número da encomenda, se disponível; não envie dados do cartão.",
    ),
    "ACCOUNT_LOGIN": (
        "Descreva o erro de acesso, sem partilhar a palavra-passe ou códigos, para eu orientar o passo de recuperação da conta.",
        "Diga o que acontece ao iniciar sessão; não partilhe palavras-passe nem códigos de verificação.",
    ),
    "PRODUCT_QUESTION": (
        "Indique o modelo do produto e a característica ou especificação que pretende verificar.",
        "Diga qual é o modelo do produto e que característica pretende conhecer.",
    ),
    "ORDER_STATUS": (
        "Indique o número da encomenda e a atualização mais recente do rastreio para eu ajudar a verificar o estado.",
        "Partilhe o número da encomenda e o que aparece no rastreio para eu ajudar a interpretar o estado.",
    ),
    "CLOSING_THANKS": (
        "Posso continuar a ajudar se ainda houver alguma questão por resolver.",
        "Se surgir outra questão, diga-me o que precisa e indicarei o próximo passo.",
    ),
    "GREETING": (
        "Diga-me com o que precisa de ajuda e indicarei o próximo passo.",
        "Partilhe a sua questão e ajudarei a identificar um próximo passo útil.",
    ),
    "COMPLAINT_GENERAL": (
        "Descreva o que aconteceu e indique o número da encomenda se a questão for sobre uma encomenda.",
        "Diga-me o que correu mal; se for sobre uma encomenda, inclua o respetivo número.",
    ),
    "UNKNOWN": (
        "Posso ajudar com uma questão da NovaShop.",
        "Diga-me o que gostaria de saber e posso sugerir um próximo passo.",
    ),
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


def _step(steps, intent, turn_index, subject):
    template = _variant(steps.get(intent, steps["UNKNOWN"]), turn_index)
    return template.format(subject=subject)


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
        step = _step(_PT_STEPS, intent, turn_index, subject)
        if intent == "UNKNOWN" and "no_affect_words" in flags:
            step = _variant(
                (
                    "Diga-me mais sobre a sua questão. Se for sobre uma "
                    "encomenda, indique o número da encomenda.",
                    "Se a questão for sobre uma encomenda, partilhe o número "
                    "da encomenda "
                    "e diga que informação precisa.",
                ),
                turn_index,
            )
        problem = _problem(intent, entities, language)
        pattern = _variant(_PT_ACTION_PATTERNS[action], turn_index)
    else:
        step = _step(_EN_STEPS, intent, turn_index, subject)
        if intent == "UNKNOWN" and "no_affect_words" in flags:
            step = _variant(
                (
                    "Tell me more about your question. If it concerns an "
                    "order, please include the order number.",
                    "If this is about an order, share its number and tell me "
                    "what information you need.",
                ),
                turn_index,
            )
        problem = _problem(intent, entities, language)
        pattern = _variant(_EN_ACTION_PATTERNS[action], turn_index)
    return pattern.format(step=step, problem=problem)
