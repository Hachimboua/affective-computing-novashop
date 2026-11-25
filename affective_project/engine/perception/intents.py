"""Keyword-based support intent and simple entity extraction."""
import re
import unicodedata

from .text_matching import matching_phrases


_CUES = {
    "en": {
        "HUMAN_REQUEST": (
            "real person",
            "human agent",
            "talk to a person",
            "speak to a person",
            "connect me with",
            "manager",
            "supervisor",
            "human",
            "agent",
        ),
        "DELIVERY_DELAY": (
            "late",
            "delay",
            "delayed",
            "not arrived",
            "still not arrived",
            "never arrive",
            "never arrived",
            "ever arrive",
            "not delivered",
            "never delivered",
            "supposed to be here",
            "waiting for",
        ),
        "DAMAGED_OR_DEFECTIVE": (
            "broken",
            "damaged",
            "defective",
            "cracked",
            "does not work",
            "doesn't work",
            "not working",
            "stopped working",
        ),
        "WRONG_ITEM": (
            "wrong item",
            "incorrect item",
            "sent the wrong",
            "not what i ordered",
        ),
        "REFUND_RETURN": (
            "refund",
            "return",
            "money back",
            "reimburse",
            "send it back",
        ),
        "PAYMENT_BILLING": (
            "payment",
            "charged",
            "charge",
            "billing",
            "invoice",
            "bill",
        ),
        "ACCOUNT_LOGIN": (
            "login",
            "log in",
            "password",
            "sign in",
            "account locked",
        ),
        "PRODUCT_QUESTION": (
            "warranty",
            "compatible",
            "available",
            "specification",
            "feature",
            "how does",
        ),
        "ORDER_STATUS": (
            "where is my order",
            "order status",
            "track my order",
            "tracking",
            "delivery status",
            "my order",
        ),
        "CLOSING_THANKS": (
            "thank you",
            "thanks",
            "that is all",
            "that's all",
            "goodbye",
            "have a good day",
        ),
        "GREETING": ("hello", "hi", "good morning", "good afternoon"),
        "COMPLAINT_GENERAL": (
            "complaint",
            "unacceptable",
            "frustrating",
            "very upset",
            "terrible service",
        ),
    },
    "pt": {
        "HUMAN_REQUEST": (
            "pessoa real",
            "agente humano",
            "falar com uma pessoa",
            "falar com um agente",
            "gerente",
            "supervisor",
            "atendente",
        ),
        "DELIVERY_DELAY": (
            "atrasado",
            "atrasada",
            "atraso",
            "não chegou",
            "ainda não chegou",
            "nunca chega",
            "nunca chegou",
            "não foi entregue",
            "à espera",
        ),
        "DAMAGED_OR_DEFECTIVE": (
            "partido",
            "partida",
            "danificado",
            "danificada",
            "avariado",
            "avariada",
            "não funciona",
        ),
        "WRONG_ITEM": (
            "artigo errado",
            "produto errado",
            "enviaram o artigo errado",
        ),
        "REFUND_RETURN": (
            "reembolso",
            "devolução",
            "devolver",
            "dinheiro de volta",
        ),
        "PAYMENT_BILLING": (
            "pagamento",
            "cobrança",
            "fatura",
            "cartão",
        ),
        "ACCOUNT_LOGIN": (
            "iniciar sessão",
            "palavra-passe",
            "senha",
            "conta bloqueada",
        ),
        "PRODUCT_QUESTION": (
            "garantia",
            "compatível",
            "disponível",
            "características",
        ),
        "ORDER_STATUS": (
            "onde está a minha encomenda",
            "estado da encomenda",
            "rastreio",
            "encomenda",
            "pedido",
        ),
        "CLOSING_THANKS": (
            "obrigado",
            "obrigada",
            "muito obrigado",
            "está tudo resolvido",
            "tenha um bom dia",
        ),
        "GREETING": ("olá", "bom dia", "boa tarde"),
        "COMPLAINT_GENERAL": (
            "reclamação",
            "inaceitável",
            "frustrado",
            "frustrada",
        ),
    },
}
_CUE_INTENTS = {}
_LANGUAGE_CUES = {}
for _language, _intents in _CUES.items():
    _cue_intents = {}
    for _intent, _cues in _intents.items():
        for _cue in _cues:
            _cue_intents.setdefault(_cue, set()).add(_intent)
    _CUE_INTENTS[_language] = _cue_intents
    _LANGUAGE_CUES[_language] = tuple(_cue_intents)

_PRODUCTS = {
    "laptop": ("laptop", "notebook", "portátil"),
    "phone": ("phone", "smartphone", "telemóvel", "celular"),
    "headphones": ("headphones", "earbuds", "auscultadores", "fones"),
    "keyboard": ("keyboard", "teclado"),
    "mouse": ("mouse", "rato"),
    "charger": ("charger", "carregador"),
    "tablet": ("tablet", "tablete"),
    "router": ("router", "roteador"),
}
_ORDER_NUMBER_RE = re.compile(
    r"\b(?:order|pedido|encomenda)\s*(?:#|number|no\.?|nº|número)?\s*(\d{3,8})\b",
    re.IGNORECASE,
)
_PRODUCT_TERMS = tuple(
    term for terms in _PRODUCTS.values() for term in terms
)


def _candidate_languages(language):
    if language == "mixed":
        return ("en", "pt")
    if language in ("en", "pt"):
        return (language,)
    return ()


def detect_intent(text, language):
    """Choose one support intent; explicit human requests take precedence."""
    normalized = unicodedata.normalize("NFKC", text).lower()
    languages = _candidate_languages(language)
    matched_cues = set()
    for candidate in languages:
        matched_cues.update(
            matching_phrases(normalized, _LANGUAGE_CUES[candidate])
        )
    matched_intents = {
        intent
        for candidate in languages
        for cue in matched_cues
        for intent in _CUE_INTENTS[candidate].get(cue, ())
    }

    if "HUMAN_REQUEST" in matched_intents:
        intent = "HUMAN_REQUEST"
    else:
        priority = (
            "REFUND_RETURN",
            "DELIVERY_DELAY",
            "DAMAGED_OR_DEFECTIVE",
            "WRONG_ITEM",
            "PAYMENT_BILLING",
            "ACCOUNT_LOGIN",
            "PRODUCT_QUESTION",
            "ORDER_STATUS",
            "CLOSING_THANKS",
            "GREETING",
            "COMPLAINT_GENERAL",
        )
        intent = "UNKNOWN"
        for candidate_intent in priority:
            if candidate_intent in matched_intents:
                intent = candidate_intent
                break

    entities = {}
    order_match = _ORDER_NUMBER_RE.search(normalized)
    if order_match:
        entities["order_number"] = order_match.group(1)
    matched_products = matching_phrases(normalized, _PRODUCT_TERMS)
    for product, terms in _PRODUCTS.items():
        if any(term in matched_products for term in terms):
            entities["product"] = product
            break
    return intent, entities
