# Sistema de Cadastro de Pessoas

Um sistema completo de cadastro de pessoas desenvolvido em Python com validação robusta, persistência em banco de dados e interface de linha de comando.

## 🚀 Características

- **Validação de Dados**: Validação completa de CPF brasileiro, email e data de nascimento
- **Banco de Dados**: Persistência com SQLite
- **CRUD Completo**: Criar, Ler, Atualizar e Deletar registros
- **Busca Avançada**: Busca por nome, CPF ou email
- **Interface CLI**: Interface de linha de comando intuitiva
- **Testes Unitários**: Cobertura completa de testes
- **Tratamento de Erros**: Mensagens de erro claras em português

## 📋 Requisitos

- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/evertontessari/Sistema-de-cadastros-de-pessoas-.git
cd Sistema-de-cadastros-de-pessoas-
```

2. Instale as dependências (opcional, apenas para testes):
```bash
pip install -r requirements.txt
```

## 💻 Uso

### Executar o Sistema

```bash
python main.py
```

### Menu Principal

O sistema oferece as seguintes opções:

1. **Adicionar nova pessoa**: Cadastrar uma nova pessoa no sistema
2. **Listar todas as pessoas**: Exibir todos os cadastros
3. **Buscar pessoa**: Buscar por nome, CPF ou email
4. **Atualizar cadastro**: Modificar informações de uma pessoa
5. **Remover pessoa**: Excluir um cadastro
6. **Estatísticas**: Visualizar estatísticas do sistema
0. **Sair**: Encerrar o programa

### Exemplo de Cadastro

```
Nome completo: João Silva
CPF (apenas números): 12345678909
Email: joao@example.com
Data de nascimento (YYYY-MM-DD): 1990-01-15
Telefone (opcional): 11999999999
Endereço (opcional): Rua das Flores, 123
```

## 🧪 Executar Testes

```bash
pytest
```

Para ver cobertura de testes:
```bash
pytest --cov=. --cov-report=html
```

## 📁 Estrutura do Projeto

```
Sistema-de-cadastros-de-pessoas-/
├── main.py           # Interface CLI principal
├── person.py         # Modelo de Person com validações
├── database.py       # Gerenciador de banco de dados
├── test_person.py    # Testes para Person
├── test_database.py  # Testes para DatabaseManager
├── requirements.txt  # Dependências do projeto
├── .gitignore       # Arquivos a serem ignorados pelo Git
└── README.md        # Este arquivo
```

## 🔒 Validações

### CPF
- Deve conter exatamente 11 dígitos
- Não pode ter todos os dígitos iguais
- Validação dos dígitos verificadores
- Aceita formatação (pontos e hífen)

### Email
- Formato válido de email
- Convertido automaticamente para minúsculas

### Data de Nascimento
- Formato: YYYY-MM-DD
- Não pode ser no futuro
- Limite máximo de 150 anos

### Nome
- Mínimo de 3 caracteres
- Não pode estar vazio

## 🛠️ Melhorias Implementadas

Este sistema foi desenvolvido com as seguintes melhorias de qualidade:

1. **Arquitetura Modular**: Separação clara entre modelo, persistência e interface
2. **Validação Robusta**: Validação completa de dados brasileiros (CPF)
3. **Tratamento de Erros**: Mensagens de erro claras e específicas
4. **Persistência de Dados**: Banco de dados SQLite para armazenamento permanente
5. **Testes Automatizados**: Cobertura completa com pytest
6. **Código Limpo**: Documentação inline, type hints e padrões PEP 8
7. **Interface Amigável**: CLI intuitiva em português
8. **Segurança**: Validação de CPF único, prevenção de SQL injection

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer um Fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abrir um Pull Request

## 📝 Licença

Este projeto é de código aberto e está disponível para uso livre.

## 👤 Autor

Everton Tessari

## 📞 Suporte

Para reportar bugs ou sugerir melhorias, abra uma issue no GitHub.