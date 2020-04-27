set -euxo
TAG=$1
docker build -t haukurp/moses-smt:$TAG $(dirname "$0")
docker push haukurp/moses-smt:$TAG