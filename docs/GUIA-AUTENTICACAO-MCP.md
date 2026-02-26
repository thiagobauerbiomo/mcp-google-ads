# Guia de Autenticação — MCP Google Ads

> Documentação completa de como configurar, trocar credenciais e resolver problemas de autenticação do MCP Google Ads no Claude Code.
>
> **Última atualização:** 2026-02-26
> **Contexto:** Migração de credenciais de caio@biomo.com.br para thiago@biomo.com.br

---

## Índice

1. [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2. [Pré-requisitos](#2-pré-requisitos)
3. [Configuração do OAuth2 no Google Cloud](#3-configuração-do-oauth2-no-google-cloud)
4. [Gerando o Refresh Token](#4-gerando-o-refresh-token)
5. [Configurando o .mcp.json](#5-configurando-o-mcpjson)
6. [Como o Claude Code Carrega as Credenciais](#6-como-o-claude-code-carrega-as-credenciais)
7. [Trocando Credenciais (Passo a Passo)](#7-trocando-credenciais-passo-a-passo)
8. [Verificação e Testes](#8-verificação-e-testes)
9. [Troubleshooting](#9-troubleshooting)
10. [Incidente 2026-02-25: Post-Mortem Completo](#10-incidente-2026-02-25-post-mortem-completo)

---

## 1. Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                       Claude Code                           │
│                                                             │
│  1. Lê ~/.claude/.mcp.json (config dos MCPs)                │
│  2. Pode cachear env vars em ~/.claude.json                 │
│     (projects["/home/thiago"]["mcpServers"])                 │
│  3. Inicia processo MCP com env vars via subprocess         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐   │
│  │              Processo MCP (subprocess)                │   │
│  │                                                       │   │
│  │  uv run --directory .../mcp-google-ads mcp-google-ads │   │
│  │                                                       │   │
│  │  ENV VARS injetadas pelo Claude Code:                 │   │
│  │    GOOGLE_ADS_CLIENT_ID                               │   │
│  │    GOOGLE_ADS_CLIENT_SECRET                           │   │
│  │    GOOGLE_ADS_DEVELOPER_TOKEN                         │   │
│  │    GOOGLE_ADS_REFRESH_TOKEN                           │   │
│  │    GOOGLE_ADS_LOGIN_CUSTOMER_ID                       │   │
│  │                                                       │   │
│  │  config.py → lê os.environ                            │   │
│  │  auth.py   → singleton GoogleAdsClient                │   │
│  │              (não recarrega se já criado)              │   │
│  └───────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│                   Google Ads API v23                          │
│                   (OAuth2 + MCC 2485256891)                   │
└─────────────────────────────────────────────────────────────┘
```

### Fluxo de Autenticação

1. Claude Code inicia → lê `~/.claude/.mcp.json`
2. Para cada MCP habilitado, inicia um subprocess (`uv run ...`)
3. As env vars do `.mcp.json` são passadas ao subprocess via `environ`
4. O MCP server (`server.py`) importa `config.py` que lê `os.environ`
5. `auth.py` cria um singleton `GoogleAdsClient` com as credenciais
6. O client usa OAuth2 (refresh_token) para obter access_tokens automaticamente
7. Todas as chamadas à API usam o mesmo singleton

### Arquivos Envolvidos

| Arquivo | Função |
|---------|--------|
| `~/.claude/.mcp.json` | **Fonte da verdade** — credenciais e config dos MCPs |
| `~/.claude.json` | Estado interno do Claude Code — pode cachear credenciais |
| `src/mcp_google_ads/config.py` | Lê env vars e valida campos obrigatórios |
| `src/mcp_google_ads/auth.py` | Cria singleton GoogleAdsClient via OAuth2 |

---

## 2. Pré-requisitos

- **Projeto GCP** com Google Ads API habilitada
- **OAuth2 Client ID** (tipo Desktop) criado no Google Cloud Console
- **Conta Google** com acesso ao MCC do Google Ads (2485256891)
- **Developer Token** aprovado (básico ou padrão)
- **uv** instalado (`~/.local/bin/uv`)
- **Claude Code** instalado e configurado

---

## 3. Configuração do OAuth2 no Google Cloud

### 3.1 Criar Projeto GCP (se não existir)

1. Acessar [Google Cloud Console](https://console.cloud.google.com)
2. Criar novo projeto ou usar existente
3. Habilitar a **Google Ads API**:
   - Menu → APIs & Services → Library
   - Buscar "Google Ads API" → Enable

### 3.2 Criar OAuth2 Client ID

1. Menu → APIs & Services → Credentials
2. Create Credentials → OAuth client ID
3. **Application type:** Desktop app
4. **Name:** MCP Google Ads (ou similar)
5. Anotar:
   - **Client ID:** `XXXXX.apps.googleusercontent.com`
   - **Client Secret:** `GOCSPX-XXXXX`

### 3.3 Configurar Tela de Consentimento (OAuth Consent Screen)

1. Menu → APIs & Services → OAuth consent screen
2. User type: **External** (ou Internal se workspace Google)
3. Adicionar escopo: `https://www.googleapis.com/auth/adwords`
4. Adicionar o email do usuário como **Test user** (se app em modo Testing)

> **IMPORTANTE:** Se o app estiver em modo "Testing", apenas os emails listados em "Test users" podem gerar tokens. Se trocar de usuário (ex: caio→thiago), o novo email DEVE ser adicionado como test user.

---

## 4. Gerando o Refresh Token

### 4.1 Método via google-ads-python (recomendado)

```bash
cd /home/thiago/projetos/mcp/mcp-google-ads

# Ativar o venv do projeto
source .venv/bin/activate

# Rodar o script de autenticação do google-ads
python -c "
from google_ads_api_auth import main
main()
"
```

Se o script acima não existir, usar o método manual:

### 4.2 Método Manual (OAuth2 Playground ou curl)

**Passo 1 — Gerar Authorization Code:**

Abrir no navegador (substituir CLIENT_ID):

```
https://accounts.google.com/o/oauth2/v2/auth?client_id=SEU_CLIENT_ID&redirect_uri=urn:ietf:wg:oauth:2.0:oob&scope=https://www.googleapis.com/auth/adwords&response_type=code&access_type=offline&prompt=consent
```

- Fazer login com a conta correta (ex: thiago@biomo.com.br)
- Autorizar o acesso
- Copiar o **authorization code**

**Passo 2 — Trocar Authorization Code por Refresh Token:**

```bash
curl -X POST https://oauth2.googleapis.com/token \
  -d "code=AUTHORIZATION_CODE" \
  -d "client_id=SEU_CLIENT_ID" \
  -d "client_secret=SEU_CLIENT_SECRET" \
  -d "redirect_uri=urn:ietf:wg:oauth:2.0:oob" \
  -d "grant_type=authorization_code"
```

A resposta terá:
```json
{
  "access_token": "ya29.XXXXX",
  "refresh_token": "1//0hXXXXX",
  "scope": "https://www.googleapis.com/auth/adwords",
  "token_type": "Bearer"
}
```

> **ANOTAR o refresh_token** — ele só aparece nesta resposta. Se perder, precisa repetir o processo.

### 4.3 Validar o Refresh Token

```bash
# Testar se o token funciona (substituir valores)
cd /home/thiago/projetos/mcp/mcp-google-ads

GOOGLE_ADS_DEVELOPER_TOKEN="SEU_DEVELOPER_TOKEN" \
GOOGLE_ADS_LOGIN_CUSTOMER_ID="2485256891" \
GOOGLE_ADS_CLIENT_ID="SEU_CLIENT_ID" \
GOOGLE_ADS_CLIENT_SECRET="SEU_CLIENT_SECRET" \
GOOGLE_ADS_REFRESH_TOKEN="SEU_REFRESH_TOKEN" \
uv run python -c "
from mcp_google_ads.auth import get_client
client = get_client()
service = client.get_service('CustomerService')
response = service.list_accessible_customers()
ids = [r.split('/')[-1] for r in response.resource_names]
print(f'Contas: {ids}')
print(f'Total: {len(ids)}')
"
```

**Resultado esperado:**
```
Contas: ['2485256891', '4025394370', '3221697754']
Total: 3
```

Se retornar 0 contas ou erro, o token está inválido ou o usuário não tem acesso ao MCC.

---

## 5. Configurando o .mcp.json

### 5.1 Localização

O arquivo fica em: **`~/.claude/.mcp.json`**

```
/home/thiago/.claude/.mcp.json
```

### 5.2 Estrutura Completa (estado atual funcionando)

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "/home/thiago/.local/bin/uv",
      "args": ["run", "--directory", "/home/thiago/projetos/mcp/mcp-google-ads", "mcp-google-ads"],
      "env": {
        "GOOGLE_ADS_DEVELOPER_TOKEN": "jgXYH9-ZRtvV76HQfCoaTQ",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "2485256891",
        "GOOGLE_ADS_CLIENT_ID": "<CLIENT_ID_DO_PROJETO_GCP>.apps.googleusercontent.com",
        "GOOGLE_ADS_CLIENT_SECRET": "GOCSPX-<SECRET>",
        "GOOGLE_ADS_REFRESH_TOKEN": "1//<REFRESH_TOKEN>"
      }
    }
  }
}
```

### 5.3 Campos Obrigatórios

| Campo | Descrição | Onde Encontrar |
|-------|-----------|----------------|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Token do desenvolvedor da API | Google Ads → Ferramentas → Centro da API |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | ID do MCC (sem hífens) | Google Ads → ID no topo da página |
| `GOOGLE_ADS_CLIENT_ID` | OAuth2 Client ID | Google Cloud Console → Credentials |
| `GOOGLE_ADS_CLIENT_SECRET` | OAuth2 Client Secret | Google Cloud Console → Credentials |
| `GOOGLE_ADS_REFRESH_TOKEN` | Refresh token do OAuth2 | Gerado no passo 4 |

> **ATENÇÃO:** O `CLIENT_ID` e `CLIENT_SECRET` são do **projeto GCP**, não do Google Ads. Se trocar de projeto GCP, ambos mudam.

---

## 6. Como o Claude Code Carrega as Credenciais

### 6.1 Fluxo Normal (sem cache)

```
Claude Code inicia
    │
    ▼
Lê ~/.claude/.mcp.json
    │
    ▼
Para cada servidor em mcpServers:
    │
    ├─ Verifica se está em enabledMcpjsonServers
    │
    ├─ Inicia subprocess com env vars do .mcp.json
    │
    └─ Conecta via JSON-RPC (stdin/stdout)
```

### 6.2 O Cache Problemático (~/.claude.json)

O Claude Code mantém um arquivo `~/.claude.json` com estado interno. Dentro dele, pode existir um cache de credenciais MCP:

```json
{
  "projects": {
    "/home/thiago": {
      "mcpServers": {
        "google-ads": {
          "env": {
            "GOOGLE_ADS_CLIENT_ID": "VALOR_CACHEADO",
            "GOOGLE_ADS_REFRESH_TOKEN": "VALOR_CACHEADO"
          }
        }
      },
      "enabledMcpjsonServers": ["google-ads", "dev", "google-tag-manager"]
    }
  }
}
```

**PROBLEMA:** Se esse cache existir, o Claude Code pode usar os valores cacheados MESMO que o `.mcp.json` tenha sido atualizado. Isso acontece porque:

1. O Claude Code lê `~/.claude.json` ao iniciar
2. Se encontrar `mcpServers` no cache do projeto, usa essas credenciais
3. O `.mcp.json` pode ser ignorado parcial ou totalmente
4. O cache em memória persiste durante toda a sessão
5. O `/mcp reconnect` reconecta ao processo existente sem matar/recriar

### 6.3 O Singleton no auth.py

O `auth.py` usa um padrão singleton:

```python
_client: GoogleAdsClient | None = None

def get_client() -> GoogleAdsClient:
    global _client
    if _client is not None:
        return _client  # RETORNA O ANTIGO, NUNCA RECRIA
    # ... cria novo client
```

Isso significa que mesmo que as env vars mudassem em runtime (não mudam), o client antigo seria usado.

**Consequência:** Para trocar credenciais, é OBRIGATÓRIO matar o processo MCP e iniciar um novo.

---

## 7. Trocando Credenciais (Passo a Passo)

### Cenário: trocar de usuário (ex: caio@biomo.com.br → thiago@biomo.com.br)

#### Passo 1 — Gerar novo Refresh Token

Seguir a [Seção 4](#4-gerando-o-refresh-token) com a conta do novo usuário.

#### Passo 2 — Se trocou de projeto GCP, atualizar Client ID e Secret

Se o novo usuário usa um projeto GCP diferente, obter novo CLIENT_ID e CLIENT_SECRET.

#### Passo 3 — Atualizar o .mcp.json

```bash
# Editar o arquivo
nano ~/.claude/.mcp.json

# Atualizar os 3 campos (ou 5 se trocou de projeto GCP):
# - GOOGLE_ADS_CLIENT_ID      (se trocou projeto GCP)
# - GOOGLE_ADS_CLIENT_SECRET   (se trocou projeto GCP)
# - GOOGLE_ADS_REFRESH_TOKEN   (SEMPRE ao trocar usuário)
```

#### Passo 4 — Validar localmente ANTES de mexer no Claude Code

```bash
cd /home/thiago/projetos/mcp/mcp-google-ads

GOOGLE_ADS_DEVELOPER_TOKEN="jgXYH9-ZRtvV76HQfCoaTQ" \
GOOGLE_ADS_LOGIN_CUSTOMER_ID="2485256891" \
GOOGLE_ADS_CLIENT_ID="NOVO_CLIENT_ID" \
GOOGLE_ADS_CLIENT_SECRET="NOVO_SECRET" \
GOOGLE_ADS_REFRESH_TOKEN="NOVO_TOKEN" \
uv run python -c "
from mcp_google_ads.auth import get_client
client = get_client()
service = client.get_service('CustomerService')
response = service.list_accessible_customers()
ids = [r.split('/')[-1] for r in response.resource_names]
print(f'Contas: {ids}')
print(f'Total: {len(ids)}')
"
```

Se retornar as contas corretamente, o token está OK. Prosseguir.

#### Passo 5 — Limpar cache do Claude Code (CRÍTICO)

```bash
# Remover cache de credenciais MCP do .claude.json
python3 -c "
import json

with open('/home/thiago/.claude.json') as f:
    data = json.load(f)

proj = data.get('projects', {}).get('/home/thiago', {})

# Remover cache de mcpServers (credenciais antigas)
if 'mcpServers' in proj:
    del proj['mcpServers']
    print('Cache mcpServers REMOVIDO')
else:
    print('Sem cache mcpServers (OK)')

with open('/home/thiago/.claude.json', 'w') as f:
    json.dump(data, f, indent=2)

print('Arquivo salvo.')
"
```

#### Passo 6 — Matar processos MCP antigos

```bash
# Matar TODOS os processos MCP google-ads
pkill -f "mcp-google-ads" 2>/dev/null

# Confirmar que morreram
ps aux | grep "mcp-google-ads" | grep -v grep || echo "Processos mortos OK"
```

#### Passo 7 — Reiniciar o Claude Code

```bash
# Sair completamente do Claude Code (NÃO basta /mcp reconnect)
# Ctrl+C ou digitar /exit

# Reabrir
claude
```

> **IMPORTANTE:** O `/mcp` reconnect NÃO é suficiente. Ele reconecta ao processo existente ou inicia um novo usando o cache em memória da sessão atual. É necessário fechar e reabrir o Claude Code completamente.

#### Passo 8 — Verificar

Dentro do Claude Code, pedir para testar:

```
list_accessible_customers
```

Deve retornar as contas do novo usuário.

#### Passo 9 — Verificação extra (conferir env vars do processo)

```bash
# Encontrar PID do processo MCP
PID=$(ps aux | grep "mcp-google-ads" | grep python3 | grep -v grep | awk '{print $2}' | head -1)

# Ver as env vars que o processo recebeu
cat /proc/$PID/environ | tr '\0' '\n' | grep "GOOGLE_ADS"
```

Confirmar que CLIENT_ID e REFRESH_TOKEN são os novos valores.

---

## 8. Verificação e Testes

### 8.1 Checklist de Verificação

```
[ ] .mcp.json tem as credenciais corretas
[ ] Teste local retorna contas (uv run python -c "...")
[ ] Cache mcpServers removido do .claude.json
[ ] Processos MCP antigos mortos
[ ] Claude Code reiniciado (não apenas /mcp reconnect)
[ ] list_accessible_customers retorna contas no Claude Code
[ ] /proc/PID/environ mostra credenciais corretas
```

### 8.2 Teste Rápido de Saúde

```bash
# Verifica tudo de uma vez
python3 -c "
import json, subprocess, os

print('=== 1. .mcp.json ===')
with open(os.path.expanduser('~/.claude/.mcp.json')) as f:
    mcp = json.load(f)
env = mcp['mcpServers']['google-ads']['env']
print(f'  CLIENT_ID: {env[\"GOOGLE_ADS_CLIENT_ID\"][:20]}...')
print(f'  TOKEN: {env[\"GOOGLE_ADS_REFRESH_TOKEN\"][:20]}...')
print(f'  LOGIN_CUSTOMER: {env[\"GOOGLE_ADS_LOGIN_CUSTOMER_ID\"]}')

print()
print('=== 2. Cache .claude.json ===')
with open(os.path.expanduser('~/.claude.json')) as f:
    data = json.load(f)
proj = data.get('projects', {}).get('/home/thiago', {})
cache = proj.get('mcpServers')
print(f'  mcpServers cache: {\"EXISTE (PROBLEMA!)\" if cache else \"None (OK)\"}')

print()
print('=== 3. Processos MCP ===')
result = subprocess.run(['pgrep', '-fa', 'mcp-google-ads'], capture_output=True, text=True)
if result.stdout.strip():
    for line in result.stdout.strip().split('\n'):
        pid = line.split()[0]
        print(f'  PID {pid} rodando')
else:
    print('  Nenhum processo (MCP não iniciado)')
"
```

---

## 9. Troubleshooting

### Problema: list_accessible_customers retorna 0 contas

**Causa mais provável:** processo MCP usando credenciais antigas.

**Solução:**
1. Verificar `/proc/PID/environ` do processo MCP
2. Se as env vars estão erradas → seguir [Seção 7](#7-trocando-credenciais-passo-a-passo) completa
3. Se as env vars estão certas → o token pode ter sido revogado ou o usuário não tem acesso ao MCC

### Problema: MCP servers não aparecem no Claude Code

**Causa mais provável:** `enabledMcpjsonServers` vazio ou None no `.claude.json`.

**Solução:**
1. Fechar Claude Code
2. Verificar: `python3 -c "import json; d=json.load(open('/home/thiago/.claude.json')); print(d.get('projects',{}).get('/home/thiago',{}).get('enabledMcpjsonServers'))"`
3. Se estiver None ou `[]`, NÃO editar manualmente — abrir Claude Code e usar `/mcp` para habilitar os servidores pela interface
4. Editar manualmente esse campo é frágil: o Claude Code pode sobrescrever na próxima sessão

### Problema: /mcp reconnect não atualiza credenciais

**Isso é esperado.** O `/mcp reconnect`:
- Reconecta ao processo MCP existente (se ainda estiver rodando)
- OU inicia novo processo com as env vars da sessão atual (que podem estar cacheadas em memória)
- NÃO relê o `.mcp.json` do disco

**Solução:** Sempre fechar e reabrir o Claude Code completamente.

### Problema: Claude Code sobrescreve .claude.json com valores antigos

**Causa:** O Claude Code salva o estado interno em memória periodicamente. Se ele tem credenciais antigas em memória, vai sobrescrever qualquer edição manual.

**Solução:**
1. Fechar Claude Code PRIMEIRO
2. Só então editar o `.claude.json`
3. Reabrir Claude Code

### Problema: Token revogado (user removeu acesso)

Se um usuário revogar o acesso em [Google Account Permissions](https://myaccount.google.com/permissions), o refresh_token para de funcionar.

**Solução:** Gerar novo refresh_token seguindo [Seção 4](#4-gerando-o-refresh-token).

---

## 10. Incidente 2026-02-25: Post-Mortem Completo

### Contexto

O usuário `caio@biomo.com.br` revogou o acesso OAuth2 ao app do Google Cloud. As credenciais do MCP Google Ads pararam de funcionar (0 contas retornadas). Era necessário migrar para `thiago@biomo.com.br`.

### Timeline

| Hora | Ação | Resultado |
|------|------|-----------|
| 25/fev | Caio revoga acesso OAuth2 | MCP retorna 0 contas |
| 25/fev | Gerado novo refresh_token para thiago@biomo.com.br | Token válido (testado localmente) |
| 25/fev | Atualizado `.mcp.json` com novo token | ✅ Arquivo correto |
| 25/fev | `/mcp reconnect` no Claude Code | ❌ Ainda 0 contas |
| 25/fev | Fechou/reabriu terminal | ❌ Ainda 0 contas |
| 25/fev | Verificou `/proc/PID/environ` | ❗ Processo usando token ANTIGO |
| 25/fev | Matou processos MCP | ✅ Processos mortos |
| 25/fev | `/mcp reconnect` | ❌ Novo processo, mas com token ANTIGO de novo |
| 25/fev | Descobriu cache em `~/.claude.json` | ❗ `projects["/home/thiago"]["mcpServers"]` com credenciais do Caio |
| 25/fev | Atualizou cache no `.claude.json` | ❌ Claude Code sobrescreveu com valores da memória |
| 25/fev | Removeu `mcpServers` do `.claude.json` | ❌ Esvaziou `enabledMcpjsonServers` também |
| 26/fev | Restaurou `enabledMcpjsonServers` | ❌ Claude Code resetou para None ao iniciar |
| 26/fev | Ciclo de restaurar/reiniciar várias vezes | ❌ Claude Code sempre resetava |
| 26/fev | Reinício limpo (sem cache + sem processos zumbi) | ✅ **FUNCIONOU** |

### Causa Raiz

**3 problemas simultâneos:**

1. **Cache de credenciais em `~/.claude.json`:** O Claude Code mantinha uma cópia completa das credenciais OAuth2 (CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN) em `projects["/home/thiago"]["mcpServers"]["google-ads"]["env"]`. Esse cache tinha as credenciais antigas do Caio. Atualizar apenas o `.mcp.json` não era suficiente.

2. **Processos zumbi:** O processo MCP iniciado na sessão anterior (25/fev, pts/5) continuava rodando com o token antigo. O `/mcp reconnect` se conectava a esse processo ao invés de criar um novo. Mesmo fechar o terminal não matava o processo se estava em outro pts.

3. **Cache em memória do Claude Code:** Mesmo depois de editar o `.claude.json` no disco, o Claude Code mantinha os valores antigos em memória e os sobrescrevia de volta ao salvar o estado. Editar o arquivo com o Claude Code rodando era inútil.

### O que NÃO funcionou

| Ação | Por que não funcionou |
|------|----------------------|
| Editar `.mcp.json` apenas | Claude Code usava cache do `.claude.json` |
| `/mcp reconnect` | Reconecta ao processo existente com token antigo |
| Fechar/abrir terminal | Processo MCP em outro pts continuava rodando |
| Editar `.claude.json` com Claude Code aberto | Claude Code sobrescrevia com cache em memória |
| Remover `mcpServers` do `.claude.json` | Apagou `enabledMcpjsonServers` junto, MCPs sumiram |
| Restaurar `enabledMcpjsonServers` manualmente | Claude Code resetava para None ao iniciar |

### O que FUNCIONOU (procedimento correto)

1. **Fechar Claude Code** (para liberar o lock do `.claude.json`)
2. **Matar TODOS os processos MCP:** `pkill -f "mcp-google-ads"`
3. **Atualizar `.mcp.json`** com as novas credenciais
4. **Limpar cache do `.claude.json`:** remover `projects["/home/thiago"]["mcpServers"]`
5. **NÃO mexer** em `enabledMcpjsonServers` manualmente
6. **Reabrir Claude Code** — ele lê o `.mcp.json` limpo e inicia processo novo
7. Se MCPs não aparecerem: usar `/mcp` para habilitar pela interface (isso grava o `enabledMcpjsonServers` no formato correto)

### Lições Aprendidas

1. **NUNCA confiar apenas no `/mcp reconnect`** — ele não resolve problemas de credenciais
2. **SEMPRE verificar `/proc/PID/environ`** — é a única forma de saber quais credenciais o processo MCP está realmente usando
3. **SEMPRE testar localmente primeiro** — rodar o MCP manualmente com as env vars corretas antes de mexer no Claude Code
4. **O `.claude.json` é controlado pelo Claude Code** — editar manualmente é frágil e pode ser sobrescrito
5. **O procedimento correto é: fechar Claude Code → limpar cache → matar processos → reabrir**
6. **O singleton no auth.py é proposital** — mas significa que trocar credenciais requer matar o processo

### Prevenção

Para evitar este problema no futuro:

1. **Antes de revogar acesso OAuth2 de qualquer usuário:** preparar as novas credenciais ANTES de revogar as antigas
2. **Ao trocar credenciais:** seguir o [Passo a Passo da Seção 7](#7-trocando-credenciais-passo-a-passo) completo
3. **Manter este documento atualizado** com qualquer novo comportamento descoberto do Claude Code
4. **Testar localmente sempre** antes de depender do Claude Code para validar

---

## Referência Rápida

### Credenciais Atuais (2026-02-26)

| Campo | Valor |
|-------|-------|
| Usuário OAuth2 | thiago@biomo.com.br |
| Projeto GCP | (Client ID: 50289272165-...) |
| MCC | 2485256891 |
| Developer Token | jgXYH9-ZRtvV76HQfCoaTQ |
| Config | `~/.claude/.mcp.json` |

### Comandos Úteis

```bash
# Ver credenciais do .mcp.json
python3 -c "import json; d=json.load(open('/home/thiago/.claude/.mcp.json')); e=d['mcpServers']['google-ads']['env']; print(f'CLIENT_ID: {e[\"GOOGLE_ADS_CLIENT_ID\"][:20]}...\nTOKEN: {e[\"GOOGLE_ADS_REFRESH_TOKEN\"][:20]}...')"

# Ver cache do .claude.json
python3 -c "import json; d=json.load(open('/home/thiago/.claude.json')); print(d.get('projects',{}).get('/home/thiago',{}).get('mcpServers','Sem cache (OK)'))"

# Ver env vars do processo MCP ativo
PID=$(ps aux | grep "mcp-google-ads" | grep python3 | grep -v grep | awk '{print $2}' | head -1) && cat /proc/$PID/environ | tr '\0' '\n' | grep GOOGLE_ADS

# Matar processos MCP
pkill -f "mcp-google-ads"

# Teste local de autenticação
cd /home/thiago/projetos/mcp/mcp-google-ads && uv run python -c "from mcp_google_ads.auth import get_client; c=get_client(); s=c.get_service('CustomerService'); r=s.list_accessible_customers(); print([x.split('/')[-1] for x in r.resource_names])"
```
