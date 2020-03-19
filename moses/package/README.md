# Package Moses model
To package a trained Moses model along with required dependencies:
- Phrase tables
- Reordering tables
- Language model
- Truecasing model

## Requirements
- Docker
- Logged in to DockerHub
- A trained model. The script downloads a directory from a remote server which should have all the dependencies.

## Package
```
./docker-build.sh user@remote.server:/path/on/remote/server docker-image:docker-tag
```
This will copy all the files from the `/path/on/remote/server` to the `trained_model` directory 

Example
```
./docker-build.sh haukurpj@torpaq:/work/haukurpj/final-en-is/binarised haukurp/moses-smt:final-en-is
```
## To Run
For and example to run the image see `docker-run.sh`