"""Custom exceptions for Google Ads MCP Server."""

from __future__ import annotations


class GoogleAdsMCPError(Exception):
    """Base exception for Google Ads MCP errors."""


class AuthenticationError(GoogleAdsMCPError):
    """Raised when authentication fails."""


class RateLimitError(GoogleAdsMCPError):
    """Raised when API rate limit is hit."""


class QuotaExhaustedError(GoogleAdsMCPError):
    """Raised when daily API quota is exhausted."""


# Common Google Ads API error codes → friendly messages (Portuguese)
FRIENDLY_ERROR_MESSAGES: dict[str, str] = {
    "AUTHENTICATION_ERROR": "Erro de autenticação. Verifique as credenciais OAuth2 e o refresh token.",
    "AUTHORIZATION_ERROR": "Sem permissão para acessar esta conta. Verifique se o MCC tem acesso.",
    "QUOTA_ERROR": "Cota da API excedida. Aguarde alguns minutos antes de tentar novamente.",
    "RATE_EXCEEDED": "Limite de requisições por segundo excedido. Aguarde e tente novamente.",
    "RESOURCE_NOT_FOUND": "Recurso não encontrado. Verifique se o ID está correto e a conta é acessível.",
    "INTERNAL_ERROR": "Erro interno do Google Ads. Tente novamente em alguns minutos.",
    "CAMPAIGN_BUDGET_ERROR": "Erro no orçamento da campanha. Verifique o valor (mínimo R$1/dia).",
    "KEYWORD_ERROR": "Erro na keyword. Verifique o texto e match type.",
    "AD_ERROR": "Erro no anúncio. Verifique headlines (max 30 chars), descriptions (max 90 chars) e URL.",
    "POLICY_VIOLATION": "Violação de política do Google Ads. O conteúdo do anúncio foi reprovado.",
    "CAMPAIGN_ERROR": "Erro na campanha. Verifique as configurações (nome, tipo, rede).",
    "MUTATE_ERROR": "Erro na operação de mutação. Verifique os campos enviados.",
    "RESOURCE_ALREADY_EXISTS": "O recurso já existe. Verifique se não há duplicatas.",
    "CRITERION_ERROR": "Erro no critério (keyword/targeting). Verifique os valores.",
    "STRING_LENGTH_ERROR": "Texto excede o limite de caracteres permitido.",
    "DISTINCT_ERROR": "Itens duplicados detectados na mesma operação.",
    "NOT_ALLOWLISTED": "Operação não permitida para esta conta. Pode exigir allowlisting pelo Google.",
    "CUSTOMER_NOT_ACTIVE": "A conta está suspensa ou inativa. Verifique o status no Google Ads.",
}


def get_friendly_error(error_code: str, original_message: str = "") -> str:
    """Get a friendly error message for a Google Ads API error code.

    Returns the friendly message if available, otherwise the original message.
    """
    for key, friendly in FRIENDLY_ERROR_MESSAGES.items():
        if key in error_code.upper() or key in original_message.upper():
            return f"{friendly} (Original: {original_message})" if original_message else friendly
    return original_message or error_code
