set -x

minikube start --namespace="arkouda"

kubectl create namespace arkouda
kubectl create secret generic sshkey --from-file=id_rsa=./keys/mykey --from-file=id_rsa.pub=./keys/mykey.pub

kubectl apply -f arkouda-udp-server/serviceaccount.yaml
kubectl apply -f arkouda-udp-server/serviceaccount-token.yaml

minikube image load arifthpe/arkouda-udp-server:latest
