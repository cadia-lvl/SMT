TAG=$1
docker build -f corpus-Dockerfile -t haukurp/moses-lvl:$TAG .
docker push haukurp/moses-lvl:$TAG