#!/bin/sh
# Sair imediatamente se um comando falhar
set -e

# Opcional: Adicionar um loop para esperar o banco de dados estar realmente pronto,
# embora depends_on: condition: service_healthy já ajude muito.
# host_db="db" # Nome do serviço do banco de dados
# count=0
# while ! nc -z "$host_db" 5432; do
#   count=$((count+1))
#   if [ $count -gt 30 ]; then # Tentar por 30 segundos
#     echo "Erro: Timeout esperando pelo banco de dados $host_db:5432"
#     exit 1
#   fi
#   echo "Aguardando o banco de dados ($count)..."
#   sleep 1
# done
# echo "Banco de dados está pronto!"

# Rodar as migrações do Alembic
echo "Rodando migrações do banco de dados..."
alembic upgrade head

# Executa o comando passado como argumentos para este script
# (que será o CMD do Dockerfile, ou o 'command:' do docker-compose se definido)
echo "Iniciando a aplicação (executando CMD: $@)..."
exec "$@"