# 🚀 Como Rodar o Projeto FireTools

## Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## 📋 Passo a Passo

### 1. Ativar o Ambiente Virtual

O projeto já tem um ambiente virtual criado. Para ativá-lo:

**No macOS/Linux:**
```bash
source venv/bin/activate
```

**No Windows:**
```bash
venv\Scripts\activate
```

Você saberá que está ativo quando ver `(venv)` no início da linha do terminal.

### 2. Instalar Dependências (se necessário)

Se for a primeira vez ou se adicionou novas dependências:

```bash
pip install -r requirements.txt
```

### 3. Rodar o Servidor

**Opção 1: Rodar com Flask (desenvolvimento)**
```bash
python app.py
```

**Opção 2: Rodar com Gunicorn (produção)**
```bash
gunicorn -c gunicorn.conf.py app:app
```

### 4. Acessar o Site

Abra seu navegador e acesse:
- **URL Local:** http://localhost:8080
- **Health Check:** http://localhost:8080/health

## 🔧 Variáveis de Ambiente (Opcional)

Você pode configurar variáveis de ambiente antes de rodar:

```bash
# Porta do servidor (padrão: 8080)
export PORT=8080

# Modo debug (padrão: false)
export DEBUG=true

# Tamanho máximo de upload em MB (padrão: 200)
export MAX_UPLOAD_MB=200

# Tempo de retenção de arquivos em segundos (padrão: 3600 = 1 hora)
export FILE_RETENTION_SECONDS=3600
```

## 📝 Comandos Úteis

### Limpar arquivos antigos
```bash
flask cleanup
```

### Desativar o ambiente virtual
```bash
deactivate
```

## 🛑 Parar o Servidor

Pressione `Ctrl + C` no terminal onde o servidor está rodando.

## ✅ Verificar se está funcionando

O servidor está funcionando se você conseguir acessar:
- http://localhost:8080/health
- Deve retornar: `{"status":"healthy","service":"firetools"}`

---

**Dica:** Se der erro de porta já em uso, mude a porta:
```bash
PORT=3000 python app.py
```


