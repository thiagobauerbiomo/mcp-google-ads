# MCP Google Ads Server

## Arquitetura
```
src/mcp_google_ads/
├── __init__.py        # __version__ = "0.1.0"
├── server.py          # Entry point (importa tools, roda mcp.run(), LOG_LEVEL via env)
├── coordinator.py     # Singleton FastMCP("google-ads") com instructions detalhadas (168 tools)
├── auth.py            # GoogleAdsClient singleton via OAuth2 (retry com backoff exponencial)
├── config.py          # GoogleAdsConfig dataclass (env vars)
├── utils.py           # Helpers: resolve_customer_id, proto_to_dict, success/error_response,
│                      #   format_micros, to_micros, validate_batch, process_partial_failure,
│                      #   check_rate_limit_error, validação GAQL (validate_status, validate_date_range,
│                      #   validate_date, validate_numeric_id, validate_enum_value, validate_limit,
│                      #   build_date_clause)
├── exceptions.py      # GoogleAdsMCPError, AuthenticationError, RateLimitError, QuotaExhaustedError,
│                      #   FRIENDLY_ERROR_MESSAGES (18 codes), get_friendly_error
└── tools/             # 23 modulos (todos com logging estruturado)
    ├── accounts.py           #  4: list_accessible_customers, get_customer_info, get_account_hierarchy, list_customer_clients
    ├── account_management.py #  3: list_account_links, get_billing_info, list_account_users
    ├── campaigns.py          #  9: list, get, create, update, set_status, remove, list_labels, set_tracking_template, clone_campaign
    ├── campaign_types.py     # 14: create_pmax, list/update_asset_groups, create_display/video/shopping/demand_gen/app, create_asset_group, add/remove/list_asset_group_assets, create/list_listing_group_filters
    ├── ad_groups.py          #  7: list, get, create, update, set_status, remove, clone_ad_group
    ├── ads.py                #  7: list, get, create_rsa, create_responsive_display_ad, update, set_status, get_strength
    ├── keywords.py           # 11: list, add, update, remove, neg_campaign, neg_ad_group, neg_shared, neg_pmax, generate_ideas, forecast, list_negative
    ├── budgets.py            #  5: list, get, create, update, remove
    ├── bidding.py            #  5: list, get, create, update, set_campaign_strategy
    ├── reporting.py          # 21: campaign/adgroup/ad/keyword perf, search_terms, audience, geo, change_history, device, hourly, age_gender, placement, quality_score, comparison, pmax_search_term_insights, pmax_network_breakdown, auction_insights, landing_page, asset_performance, shopping_performance, get_industry_benchmarks
    ├── dashboard.py          #  2: mcc_performance_summary, account_dashboard
    ├── audiences.py          # 12: list_segments, add/remove_targeting, suggest_geo, list_targeting, add/remove_audience_ad_group, create_custom_audience, add_audience/search_theme_signal, list/remove_asset_group_signals
    ├── extensions.py         # 16: list_assets, sitelinks, callouts, snippets, call, remove, image, video, lead_form, price, promotion, link_campaign, link_ad_group, unlink, unlink_customer_assets
    ├── labels.py             #  8: list, create, remove, apply_to_campaign/ad_group/ad/keyword, remove_from_resource
    ├── shared_sets.py        #  6: list, create, remove, list_members, link_to_campaign, unlink_from_campaign
    ├── conversions.py        #  6: list_actions, get_action, create_action, update_action, import_offline, list_goals
    ├── targeting.py          # 14: device_bid, create/list/remove_ad_schedule, exclude_geo, add_geo, add/remove_language, age/gender/income_bid, demographic_batch, add/list_proximity_targeting
    ├── recommendations.py    #  5: list, get, apply, dismiss, get_optimization_score
    ├── experiments.py        #  5: list, create, get, promote, end
    ├── batch.py              #  1: batch_set_status (multi-resource status changes)
    ├── diagnostics.py        #  3: campaign_health_check, validate_landing_page, budget_forecast
    ├── ai_generation.py      #  3: generate_ad_text, generate_ad_images, generate_audience_definition
    └── search.py             #  1: execute_gaql (GAQL raw)
```

## Como Rodar
```bash
uv run mcp-google-ads
# LOG_LEVEL=DEBUG uv run mcp-google-ads  (para debug)
```

## Testes
```bash
uv run pytest tests/ -v              # com cobertura
uv run ruff check src/               # linter
uv run ruff check src/ --fix         # auto-fix
```

## Como Adicionar Novo Tool
1. Criar ou editar arquivo em `tools/`
2. Importar `mcp` de `coordinator.py`
3. Decorar funcao com `@mcp.tool()`
4. Usar `Annotated[tipo, "descricao"]` para parametros
5. Retornar `success_response(data)` ou `error_response(msg)`
6. Importar no `tools/__init__.py` e no `server.py`
7. Adicionar `import logging` e `logger = logging.getLogger(__name__)`
8. Usar `logger.error("Failed to ...: %s", e, exc_info=True)` em todos os except
9. Validar TODOS os inputs do usuario antes de interpolar em GAQL

## Padrao de Resposta
```python
# Sucesso
success_response({"campaigns": [...], "count": 5}, message="Opcional")
# -> {"status": "success", "message": "...", "data": {...}}

# Erro
error_response("Descricao do erro", details={"field": "valor"})
# -> {"status": "error", "error": "...", "details": {...}}
```

## Validação GAQL (utils.py)
Todas as tools validam inputs antes de interpolar em queries GAQL:
- `validate_status(s)` — valida contra ENABLED/PAUSED/REMOVED
- `validate_numeric_id(s)` — garante que IDs são numéricos (remove hifens)
- `validate_enum_value(s)` — valida enums antes de getattr(client.enums.XXX, user_param)
- `validate_date_range(s)` — valida contra ranges permitidos (LAST_30_DAYS, etc.)
- `validate_date(s)` — valida formato YYYY-MM-DD
- `validate_limit(n, max)` — valida que limit está entre 1 e max (default 10000)
- `build_date_clause(date_range, start_date, end_date)` — constroi clausula de data GAQL (valida ordem das datas)

## Reports
Todos os 21 reports suportam datas customizadas:
- `date_range`: predefinido (LAST_7_DAYS, LAST_30_DAYS, THIS_MONTH, etc.)
- `start_date` + `end_date`: YYYY-MM-DD (tem prioridade sobre date_range)
- Default: LAST_30_DAYS (exceto change_history e hourly: LAST_7_DAYS)

## Seguranca
- Recursos criados PAUSED por default
- customer_id obrigatorio na maioria das tools
- Credenciais via env vars (nunca hardcoded)
- Logs vao para stderr (stdout reservado para JSON-RPC)
- LOG_LEVEL configurável via env var (default: INFO)
- Logging estruturado em todos os 23 modulos (logger.error com exc_info=True)
- Validação de inputs GAQL contra injection (todos os 23 modulos)
- Rate limit detection com mensagens amigáveis (check_rate_limit_error)
- 18 códigos de erro mapeados para mensagens em português (get_friendly_error)
- validate_enum_value antes de todo getattr(client.enums.XXX, user_param)
- validate_limit em todas as queries com LIMIT
- validate_date em comparison_report (4 parametros de data)
- `execute_gaql`: SELECT-only, max 10000 chars, keyword blocklist, logging
- Batch limits: max 5000 keywords/assets por chamada, 2000 conversions
- Deduplicação automática em batch de keywords (por text+match_type)
- Validação de dict params (campos obrigatórios verificados antes do envio)
- Auth com retry e backoff exponencial (3 tentativas)
- Timeout de 30s em create_image_asset (urllib)

## Testes (687 testes, 95% cobertura)
Cobertura de todos os 23 modulos de tools + utils, config, auth, server, exceptions:
```
tests/
├── conftest.py              # fixtures: mock_config, mock_google_ads_client, assert_success/error
├── test_utils.py            # 45 testes (validadores, proto_to_dict, validate_batch, check_rate_limit_error, get_friendly_error)
├── test_config.py           #  6 testes
├── test_auth.py             #  4 testes
├── test_server.py           #  2 testes (main + LOG_LEVEL)
├── test_campaigns.py        # 45 testes (9 tools incl. set_tracking_template, clone_campaign)
├── test_campaign_types.py   # 51 testes (todas as 14 tools)
├── test_ad_groups.py        # 41 testes (7 tools incl. clone_ad_group)
├── test_ads.py              # 56 testes (7 tools incl. create_responsive_display_ad)
├── test_keywords.py         # 45 testes (11 tools incl. neg_ad_group, pmax_neg)
├── test_reporting.py        # 71 testes (21 reports incl. pmax_network, auction, landing_page, asset, shopping, benchmarks)
├── test_labels.py           # 18 testes
├── test_conversions.py      # 16 testes
├── test_shared_sets.py      # 18 testes
├── test_targeting.py        # 35 testes (14 tools incl. add/list proximity)
├── test_search.py           #  7 testes
├── test_dashboard.py        #  4 testes
├── test_audiences.py        # 33 testes
├── test_bidding.py          # 26 testes
├── test_extensions.py       # 33 testes
├── test_recommendations.py  # 15 testes
├── test_experiments.py      # 14 testes
├── test_account_management.py # 7 testes
├── test_accounts.py         # 14 testes
├── test_budgets.py          # 38 testes
├── test_batch.py            # 11 testes (batch_set_status)
├── test_diagnostics.py      # 11 testes (health_check, validate_landing_page, budget_forecast)
└── test_ai_generation.py    # 10 testes (generate_ad_text, images, audience_definition)
```

Modulos com 100% cobertura (18): auth, config, coordinator, exceptions, utils, __init__, tools/__init__, accounts, account_management, audiences, batch, budgets, experiments, recommendations, search, shared_sets
Modulos acima de 95%: ads (99%), ai_generation (99%), keywords (98%), bidding (98%), campaign_types (97%), ad_groups (95%)
Modulos acima de 90%: labels (94%), diagnostics (94%), targeting (93%), server (93%), conversions (91%), reporting (91%)
Modulos acima de 85%: dashboard (89%), extensions (88%), campaigns (86%)

## Dependencias Principais
- `google-ads >= 28.0.0, < 29.0.0` (API v23, pinned major)
- `mcp[cli] >= 1.2.0` (FastMCP)
- `pydantic >= 2.0.0`
- Python >= 3.12
- Dev: `pytest >= 8.0`, `pytest-cov >= 5.0`, `pytest-mock >= 3.14`, `ruff >= 0.4.0`

## Linter (ruff)
Configurado em pyproject.toml:
- Line length: 120
- Rules: E, F, W, I, UP, B, SIM
- Ignore: E501, SIM108, SIM113
- Tests: F401, F811 ignorados

## Knowledge Base (Skills)
Referencia de estrategias e recipes em `/home/thiago/projetos/skills/agentes_ai/`:
- `05_Google_Ads_AI_Agents.md` — 5 blueprints de automacao (analise, keywords, criacao, monitoramento, audiencias)
- `06_google_ads_estrategias.md` — Estrutura full-funnel, progressao de lances, sinais, audiencias, API v23
- `07_google_ads_gaql_recipes.md` — 20+ queries GAQL prontas (performance, keywords, search terms, QS, demograficos, geo, devices, horarios, budget, concorrencia)
- `08_google_ads_checklist.md` — Checklists de setup, auditoria semanal/mensal, pre-lancamento, criterios de decisao rapida

Consultar essas skills antes de tomar decisoes de otimizacao ou criar automacoes.

## API Reference
- Campos GAQL: https://developers.google.com/google-ads/api/fields/v23/overview
- Resource names: `customers/{id}/campaigns/{id}`, etc.
- Micros: valores monetarios em micros (1 BRL = 1_000_000 micros)
