NAMESPACE='crossplane-system'

helm upgrade crossplane \
  --install \
  --create-namespace \
  --namespace "${NAMESPACE}" \
  --version 1.3.0 \
  --values values.yaml \
  crossplane-stable/crossplane

if ! kubectl get ns "${NAMESPACE}"; then
  kubectl create ns "${NAMESPACE}"
else
  echo "${NAMESPACE} exists"
fi

kubectl create secret generic aws-creds \
  --namespace "${NAMESPACE}" \
  --from-file=creds=./creds.conf

kubectl apply --filename providerconfig.yaml
kubectl apply --filename manifests/infra.yaml
