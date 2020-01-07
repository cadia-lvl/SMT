set -euxo
TAG=$1
docker build --no-cache --build-arg FRONTEND_VERSION=v$TAG -t haukurp/moses-lvl:$TAG $(dirname "$0")
docker push haukurp/moses-lvl:$TAG