# gharchive-pipeline

Pipeline de dados **em desenvolvimento** que processa eventos públicos do GitHub (fonte: [GH Archive](https://www.gharchive.org/)) e os transforma em arquivos Parquet prontos para consulta com SQL.

O projeto faz parte dos meus estudos em Engenharia de Dados e o objetivo é praticar, com dados reais e volumosos, ingestão, tratamento de esquema, armazenamento colunar e validação de qualidade.

## Status

- [x] Reconhecimento e perfilamento dos dados de um arquivo horário
- [x] Conversão de JSON compactado para Parquet com esquema explícito
- [x] Validação de contagem de linhas entre entrada e saída
- [ ] Download automatizado de um dia completo (24 arquivos)
- [ ] Parquet particionado por data
- [ ] Extração dos campos do `payload` por tipo de evento
- [ ] Verificações de qualidade (duplicatas, nulos, datas fora da hora esperada)
- [ ] Tratamento dos dados para deixá-los prontos para uso
- [ ] Testes automatizados (pytest)
- [ ] Análises em SQL com DuckDB
- [ ] Docker

## Fonte de dados

O GH Archive publica um arquivo por hora (`AAAA-MM-DD-H.json.gz`, horário UTC), com um evento do GitHub por linha. Cada evento tem campos comuns (`id`, `type`, `actor`, `repo`, `created_at`) e um `payload` cuja estrutura muda conforme o tipo de evento.

Observações do perfilamento do arquivo `2026-10-01-15` (85.569 eventos):

- `PushEvent` representa cerca de 75% dos eventos.
- O campo `org` existe em apenas ~16% dos eventos (só quando o repositório pertence a uma organização). Por isso o esquema foi definido depois de perfilar o arquivo inteiro, e não apenas um evento.

## Arquitetura

```
GH Archive (JSON.gz por hora)
   -> leitura com DuckDB (esquema explícito)
   -> campos achatados em colunas + payload mantido como JSON
   -> Parquet (compressão zstd)
   -> consultas SQL
```

## Decisões técnicas

- **DuckDB:** roda como biblioteca (sem servidor), lê JSON compactado e Parquet diretamente, usa SQL e processa dados maiores que a memória. Alternativas consideradas: pandas (carrega tudo em memória), Spark (excessivo para este volume) e PostgreSQL (exige servidor e carga prévia).
- **Parquet:** formato colunar, comprimido e tipado, adequado para consultas analíticas.
- **Esquema explícito:** os tipos de cada coluna são declarados, em vez de inferidos, para o resultado ser previsível.
- **Payload como JSON por enquanto:** a extração dos campos de cada tipo de evento é uma etapa planejada.
- **Validação:** o script compara o número de linhas de entrada e saída e interrompe com erro se forem diferentes. Isso garante que nenhuma linha foi perdida, mas ainda não valida o conteúdo das colunas.

## Como executar

Requisitos: Python 3.

```bash
git clone https://github.com/natangadonski/gharchive-pipeline.git
cd gharchive-pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

mkdir -p data/raw
wget -P data/raw https://data.gharchive.org/2026-10-01-15.json.gz

python3 src/to_parquet.py data/raw/2026-10-01-15.json.gz data/processed/2026-10-01-15.parquet
```

Saída esperada: `85569 rows written to data/processed/2026-10-01-15.parquet`.

## Estrutura do projeto

```
src/        código do pipeline
tests/      testes (a fazer)
data/       dados locais (ignorados pelo Git)
```

## Visão de longo prazo

Hoje o foco é um pipeline simples e confiável: captar o dado, tratá-lo e entregar tabelas prontas para consulta. No futuro, a ideia é evoluir o projeto para um pacote reutilizável, que outras aplicações possam importar.

## Próximos passos

Automatizar o download de um dia completo, particionar o Parquet por data, extrair os campos de cada tipo de evento, adicionar verificações de qualidade e tratamento dos dados, e incluir testes e análises em SQL (por exemplo, atividade por tipo de evento e proporção de bots).
