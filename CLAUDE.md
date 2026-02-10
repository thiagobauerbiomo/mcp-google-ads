# MCP Google Ads Server

## Arquitetura
```
src/mcp_google_ads/
├── server.py          # Entry point (importa tools, roda mcp.run())
├── coordinator.py     # Singleton FastMCP("google-ads")
├── auth.py            # GoogleAdsClient singleton via OAuth2
├── config.py          # GoogleAdsConfig dataclass (env vars)
├── utils.py           # Helpers: resolve_customer_id, proto_to_dict, success/error_response
├── exceptions.py      # Custom exceptions
└── tools/             # 11 modulos, 61 tools total
    ├── accounts.py    # 4: list_accessible_customers, get_customer_info, get_account_hierarchy, list_customer_clients
    ├── campaigns.py   # 7: list, get, create, update, set_status, remove, list_labels
    ├── ad_groups.py   # 6: list, get, create, update, set_status, remove
    ├── ads.py         # 6: list, get, create_rsa, update, set_status, get_strength
    ├── keywords.py    # 8: list, add, update, remove, neg_campaign, neg_shared, generate_ideas, forecast
    ├── budgets.py     # 4: list, get, create, update
    ├── bidding.py     # 5: list, get, create, update, set_campaign_strategy
    ├── reporting.py   # 8: campaign/adgroup/ad/keyword perf, search_terms, audience, geo, change_history
    ├── audiences.py   # 6: list_segments, add_targeting, remove_targeting, suggest_geo, list_targeting, add_audience
    ├── extensions.py  # 6: list_assets, sitelinks, callouts, snippets, call, remove
    └── search.py      # 1: execute_gaql (GAQL raw)
```

## Como Rodar
```bash
uv run mcp-google-ads
```

## Como Adicionar Novo Tool
1. Criar ou editar arquivo em `tools/`
2. Importar `mcp` de `coordinator.py`
3. Decorar funcao com `@mcp.tool()`
4. Usar `Annotated[tipo, "descricao"]` para parametros
5. Retornar `success_response(data)` ou `error_response(msg)`
6. Importar no `tools/__init__.py` e no `server.py`

## Padrao de Resposta
```python
# Sucesso
success_response({"campaigns": [...], "count": 5}, message="Opcional")
# -> {"status": "success", "message": "...", "data": {...}}

# Erro
error_response("Descricao do erro", details={"field": "valor"})
# -> {"status": "error", "error": "...", "details": {...}}
```

## Seguranca
- Recursos criados PAUSED por default
- customer_id obrigatorio na maioria das tools
- Credenciais via env vars (nunca hardcoded)
- Logs vao para stderr (stdout reservado para JSON-RPC)

## Dependencias Principais
- `google-ads >= 28.0.0` (API v23)
- `mcp[cli] >= 1.2.0` (FastMCP)
- `pydantic >= 2.0.0`
- Python >= 3.12

## API Reference
- Campos GAQL: https://developers.google.com/google-ads/api/fields/v23/overview
- Resource names: `customers/{id}/campaigns/{id}`, etc.
- Micros: valores monetarios em micros (1 BRL = 1_000_000 micros)

## Testar
```bash
# Verificar se o servidor inicia
uv run mcp-google-ads

# Testar autenticacao (usar via Claude Code)
# -> chamar list_accessible_customers
# -> chamar get_customer_info com customer_id=2485256891
```
