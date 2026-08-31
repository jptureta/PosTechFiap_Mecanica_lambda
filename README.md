# Repositório Lambda / Function Serverless

Este repositório concentra a lógica serverless da solução, responsável por eventos e processamento assíncrono fora do fluxo principal da API.

## Objetivo

- manter a função Lambda isolada do restante da arquitetura
- executar processamento assíncrono e eventos específicos
- publicar a função em ambiente cloud com automação de deploy
- manter o processo em homologação e produção com governança de branch

## Stack principal

- Python 3.12
- AWS Lambda
- AWS SAM
- boto3
- GitHub Actions

## Estrutura do repositório

```text
repo-lambda/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── src/
│   └── handler.py
├── README.md
├── requirements.txt
├── template.yaml
└── .gitignore
```

## Fluxo recomendado

```text
feature/* -> PR -> homologacao -> deploy automático
feature/* -> PR -> main -> deploy automático em produção
```

## Branches

- `homologacao`
- `main`

## CI/CD

O workflow deste repositório executa:

1. instalação das dependências
2. testes unitários
3. build do pacote SAM
4. deploy automático em homologação
5. deploy automático em produção

## Secrets obrigatórios

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

## Como usar

```bash
pip install aws-sam-cli
sam build
sam deploy --guided
```

## Observações

- a lógica serverless deve permanecer desacoplada da API principal
- o deploy depende de branch protegida e checks obrigatórios
- o código deve ser mantido mínimo, idempotente e orientado a eventos

## Regras de proteção

- commits diretos bloqueados
- merge somente via Pull Request
- revisão mínima obrigatória
- status checks obrigatórios
- bloqueio de force push
- bloqueio de exclusão da branch
