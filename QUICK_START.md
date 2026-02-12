# Guia Rápido - Sistema de Cadastro de Pessoas

## Início Rápido

### Instalação
```bash
git clone https://github.com/evertontessari/Sistema-de-cadastros-de-pessoas-.git
cd Sistema-de-cadastros-de-pessoas-
pip install -r requirements.txt  # Apenas para testes
```

### Executar o Sistema
```bash
python main.py
```

## Comandos Principais

### 1. Adicionar Pessoa
- Opção: `1`
- Campos obrigatórios: Nome, CPF, Email, Data de Nascimento
- Campos opcionais: Telefone, Endereço

### 2. Listar Pessoas
- Opção: `2`
- Mostra todas as pessoas cadastradas

### 3. Buscar Pessoa
- Opção: `3`
- Busca por: Nome, CPF ou Email
- Busca parcial (não precisa digitar completo)

### 4. Atualizar Cadastro
- Opção: `4`
- Necessita o ID da pessoa
- CPF não pode ser alterado

### 5. Remover Pessoa
- Opção: `5`
- Requer confirmação
- Ação irreversível

### 6. Estatísticas
- Opção: `6`
- Total de pessoas cadastradas
- Data do último cadastro

## Formato de Dados

### CPF
- **Formato**: 11 dígitos numéricos
- **Exemplos válidos**: 
  - `12345678909`
  - `123.456.789-09` (formatação removida automaticamente)
- **Validação**: Verifica dígitos verificadores

### Email
- **Formato**: usuario@dominio.com
- **Exemplo**: `joao@example.com`
- **Conversão**: Automaticamente convertido para minúsculas

### Data de Nascimento
- **Formato**: YYYY-MM-DD
- **Exemplo**: `1990-05-15`
- **Validação**: Não aceita datas futuras

### Telefone (opcional)
- **Formato**: Livre
- **Exemplo**: `11987654321`

### Endereço (opcional)
- **Formato**: Livre
- **Exemplo**: `Rua das Flores, 123`

## Exemplos de Uso

### Cadastro Completo
```
Nome completo: João da Silva
CPF (apenas números): 12345678909
Email: joao@example.com
Data de nascimento (YYYY-MM-DD): 1990-05-15
Telefone (opcional): 11987654321
Endereço (opcional): Rua das Flores, 123
```

### Cadastro Mínimo
```
Nome completo: Maria Santos
CPF (apenas números): 98765432100
Email: maria@example.com
Data de nascimento (YYYY-MM-DD): 1995-08-20
Telefone (opcional): [Enter para pular]
Endereço (opcional): [Enter para pular]
```

## Testes

### Executar todos os testes
```bash
pytest
```

### Executar testes específicos
```bash
pytest test_person.py         # Testes de validação
pytest test_database.py       # Testes de banco de dados
```

### Ver cobertura de testes
```bash
pytest --cov=. --cov-report=html
```

## Tratamento de Erros

### Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| "CPF deve ter 11 dígitos" | CPF com número incorreto de dígitos | Digite exatamente 11 dígitos |
| "CPF inválido" | Dígitos verificadores incorretos | Verifique o CPF digitado |
| "CPF já cadastrado no sistema" | CPF duplicado | Use outro CPF ou atualize o cadastro existente |
| "Email inválido" | Formato de email incorreto | Use formato: usuario@dominio.com |
| "Data de nascimento deve estar no formato YYYY-MM-DD" | Formato de data incorreto | Use formato: 1990-01-15 |
| "Nome deve ter pelo menos 3 caracteres" | Nome muito curto | Digite nome completo |

## Estrutura de Arquivos

```
Sistema-de-cadastros-de-pessoas-/
├── main.py              # Interface CLI
├── person.py            # Modelo Person com validações
├── database.py          # Gerenciador de banco de dados
├── test_person.py       # Testes de Person
├── test_database.py     # Testes de DatabaseManager
├── requirements.txt     # Dependências
├── README.md           # Documentação completa
├── QUICK_START.md      # Este arquivo
└── .gitignore          # Arquivos ignorados pelo Git
```

## Dicas

1. **Backup**: O banco de dados é salvo em `pessoas.db`. Faça backup regularmente.
2. **CPF único**: Cada CPF só pode ser cadastrado uma vez.
3. **Busca inteligente**: A busca funciona com texto parcial.
4. **Confirmação**: Remoções sempre pedem confirmação.
5. **Campos opcionais**: Pressione Enter para pular campos opcionais.

## Suporte

- **Documentação completa**: Ver `README.md`
- **Reportar bugs**: Abra uma issue no GitHub
- **Contribuir**: Faça um fork e envie um Pull Request
