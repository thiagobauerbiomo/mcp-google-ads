# MCP Google Ads Server

## Arquitetura
```
src/mcp_google_ads/
├── server.py          # Entry point (importa tools, roda mcp.run())
├── coordinator.py     # Singleton FastMCP("google-ads")
├── auth.py            # GoogleAdsClient singleton via OAuth2 + retry com backoff
├── config.py          # GoogleAdsConfig dataclass (env vars)
├── utils.py           # Helpers: resolve_customer_id, proto_to_dict, success/error_response, paginate, logging
├── validators.py      # Pydantic validators para inputs complexos
├── exceptions.py      # Custom exceptions
└── tools/             # 19 modulos, 123 tools total
    ├── accounts.py           #  4: list_accessible_customers, get_customer_info, get_account_hierarchy, list_customer_clients
    ├── account_management.py #  3: list_account_links, get_billing_info, list_account_users
    ├── campaigns.py          #  7: list, get, create, update, set_status, remove, list_labels
    ├── campaign_types.py     #  8: create_pmax, list/update_asset_groups, create_display/video/shopping/demand_gen/app
    ├── ad_groups.py          #  6: list, get, create, update, set_status, remove
    ├── ads.py                #  6: list, get, create_rsa, update, set_status, get_strength
    ├── keywords.py           #  8: list, add, update, remove, neg_campaign, neg_shared, generate_ideas, forecast
    ├── budgets.py            #  4: list, get, create, update
    ├── bidding.py            #  5: list, get, create, update, set_campaign_strategy
    ├── reporting.py          # 14: campaign/adgroup/ad/keyword perf, search_terms, audience, geo, change_history, device, hourly, age_gender, placement, quality_score, comparison
    ├── audiences.py          #  6: list_segments, add_targeting, remove_targeting, suggest_geo, list_targeting, add_audience
    ├── extensions.py         # 14: list_assets, sitelinks, callouts, snippets, call, remove, image, video, lead_form, price, promotion, link_campaign, link_ad_group, unlink
    ├── labels.py             #  8: list, create, remove, apply_to_campaign/ad_group/ad/keyword, remove_from_resource
    ├── shared_sets.py        #  6: list, create, remove, list_members, link_to_campaign, unlink_from_campaign
    ├── conversions.py        #  6: list_actions, get_action, create_action, update_action, import_offline, list_goals
    ├── targeting.py          #  7: device_bid, create/list/remove_ad_schedule, exclude_geo, add/remove_language
    ├── recommendations.py    #  5: list, get, apply, dismiss, get_optimization_score
    ├── experiments.py        #  5: list, create, get, promote, end
    └── search.py             #  1: execute_gaql (GAQL raw)

tests/                 # 73 testes unitarios
├── conftest.py        # Fixtures e helpers compartilhados
├── test_utils.py
├── test_config.py
├── test_auth.py
├── test_campaigns.py
├── test_ad_groups.py
├── test_ads.py
├── test_keywords.py
├── test_reporting.py
├── test_labels.py
├── test_conversions.py
├── test_shared_sets.py
└── test_targeting.py
```

## Como Rodar
```bash
uv run mcp-google-ads
```

## Testes
```bash
uv run pytest tests/ -v
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
- Retry com exponential backoff para erros transientes

## Dependencias Principais
- `google-ads >= 28.0.0` (API v23)
- `mcp[cli] >= 1.2.0` (FastMCP)
- `pydantic >= 2.0.0`
- Python >= 3.12
- Dev: `pytest >= 8.0`, `pytest-cov`, `pytest-mock`

## API Reference
- Campos GAQL: https://developers.google.com/google-ads/api/fields/v23/overview
- Resource names: `customers/{id}/campaigns/{id}`, etc.
- Micros: valores monetarios em micros (1 BRL = 1_000_000 micros)

## Testar
```bash
# Verificar se o servidor inicia
uv run mcp-google-ads

# Rodar testes unitarios
uv run pytest tests/ -v

# Testar autenticacao (usar via Claude Code)
# -> chamar list_accessible_customers
# -> chamar get_customer_info com customer_id=2485256891
```
