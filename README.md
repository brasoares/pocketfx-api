# PocketFX API

API REST para análise multi-ativo de investimentos (FX + criptomoedas) com três lentes de análise: retrospectiva, presente (média móvel) e futuro (Monte Carlo).

Projeto desenvolvido como MVP da disciplina **Desenvolvimento Backend Avançado** da Pós-Graduação em Desenvolvimento Full Stack — PUC-Rio.

## Visão geral

O PocketFX permite ao usuário cadastrar experimentos de investimento hipotéticos ("e se eu tivesse colocado X em BTC em 2020?") e analisá-los sob três perspectivas:

- **Retrospectiva**: quanto valeria hoje, comparando preço da data do aporte com preço atual.
- **Presente**: posicionamento do preço atual em relação à média móvel de 90 dias.
- **Futuro**: projeção via simulação de Monte Carlo (1000 trajetórias por padrão).

## Arquitetura

```
┌─────────────────┐         REST/HTTP        ┌──────────────────┐
│                 │ ──────────────────────▶  │                  │
│  Front-End      │                          │  PocketFX API    │
│  (Next.js)      │ ◀──────────────────────  │  (FastAPI)       │
│                 │                          │                  │
└─────────────────┘                          └────────┬─────────┘
                                                      │
                                          ┌───────────┼───────────┐
                                          │           │           │
                                          ▼           ▼           ▼
                                    ┌─────────┐ ┌──────────┐ ┌─────────┐
                                    │ SQLite  │ │Frankfurter│ │CoinGecko│
                                    │  (DB)   │ │  (FX)    │ │ (Crypto)│
                                    └─────────┘ └──────────┘ └─────────┘
```

## APIs externas utilizadas

### Frankfurter
- URL: https://api.frankfurter.dev
- Cobertura: câmbio fiat oficial do Banco Central Europeu (ECB), 31 moedas
- Cadastro: não requerido
- Licença: open-source, uso livre
- Endpoints utilizados: `/v1/{date}` (cotação histórica) e `/v1/{start}..{end}` (série temporal)

### CoinGecko (API pública gratuita)
- URL: https://api.coingecko.com
- Cobertura: criptomoedas (10.000+ ativos)
- Cadastro: não requerido para o tier público
- Limite: ~30 requisições/minuto
- Endpoints utilizados: `/api/v3/coins/{id}/history` e `/api/v3/coins/{id}/market_chart`

## Stack

- Python 3.12
- FastAPI 0.115
- SQLAlchemy 2.0
- SQLite
- Pydantic 2.9
- httpx 0.27
- numpy 2.1
- Docker

## Instalação local

Pré-requisitos: Python 3.12+, Git.

```bash
# Clone o repositório
git clone https://github.com/brasoares/pocketfx-api.git
cd pocketfx-api

# Crie e ative o ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# ou
source venv/bin/activate       # Linux/Mac

# Instale dependências
pip install -r requirements.txt

# Rode o servidor
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000`. A documentação Swagger interativa fica em `http://localhost:8000/docs`.

## Execução com Docker

```bash
# Build da imagem
docker build -t pocketfx-api .

# Rodar contêiner
docker run -p 8000:8000 pocketfx-api
```

Acesse `http://localhost:8000/docs` para a documentação interativa.

## Rotas principais

### Meta
- `GET /` — informação do serviço
- `GET /health` — health check

### Experimentos (CRUD)
- `GET /experiments` — listar (com filtro e paginação)
- `POST /experiments` — criar
- `GET /experiments/{id}` — buscar
- `PATCH /experiments/{id}` — atualizar parcialmente
- `DELETE /experiments/{id}` — apagar

### Análise (as 3 lentes)
- `GET /analysis/retrospective/{experiment_id}` — quanto valeria hoje
- `GET /analysis/present` — sinal vs. média móvel 90d
- `GET /analysis/projection` — Monte Carlo
- `GET /analysis/quote` — cotação direta

## Ativos suportados

**FX**: USD, EUR, JPY, GBP, CNY, CHF, BRL  
**Crypto**: BTC, ETH, USDC, SOL, ADA

## Estrutura do código

```
pocketfx-api/
├── app/
│   ├── main.py            # ponto de entrada FastAPI
│   ├── config.py          # constantes globais
│   ├── database.py        # conexão SQLite
│   ├── models.py          # tabelas SQLAlchemy
│   ├── schemas.py         # validação Pydantic
│   ├── routers/           # rotas HTTP por domínio
│   │   ├── meta.py
│   │   ├── experiments.py
│   │   └── analysis.py
│   └── services/          # lógica de negócio + integrações
│       ├── frankfurter.py
│       ├── coingecko.py
│       └── monte_carlo.py
├── Dockerfile
├── requirements.txt
└── README.md
```

## Aviso

Os cenários gerados pela rota de projeção são simulações estatísticas baseadas em volatilidade histórica. **Não constituem previsão de mercado nem recomendação de investimento.**

## Licença

Apache 2.0 — ver arquivo `LICENSE`.

## Autor

Henoc Soares Freire — [github.com/brasoares](https://github.com/brasoares)