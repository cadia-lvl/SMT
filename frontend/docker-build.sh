set -euxo
TAG=$1
docker build -t haukurp/moses-lvl:$TAG $(dirname "$0")
docker push haukurp/moses-lvl:$TAG