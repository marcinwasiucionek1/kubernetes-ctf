#!/bin/sh
set -e

APISERVER="https://kubernetes.default.svc"
CACERT="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"

# Configure kubectl with the in-cluster API server and CA cert.
# Credentials (token) are deliberately not set here — the student must
# discover the automounted service account token at runtime.
kubectl config set-cluster in-cluster \
  --server="${APISERVER}" \
  --certificate-authority="${CACERT}" \
  --embed-certs=true

kubectl config set-context in-cluster --cluster=in-cluster
kubectl config use-context in-cluster

exec python /app/app.py
