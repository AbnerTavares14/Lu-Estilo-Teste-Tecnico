set -e

echo "Rodando migrações do banco de dados..."
alembic upgrade head

echo "Iniciando a aplicação (executando CMD: $@)..."
exec "$@"