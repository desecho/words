#!/bin/bash

set -eou pipefail

BACKEND_CONTAINER=${BACKEND_CONTAINER:-words}
POD_ID=$(kubectl get pods -lapp="$PROJECT" | grep Running | awk '{print $1}')
kubectl exec "$POD_ID" --container "$BACKEND_CONTAINER" -- ./src/manage.py "$@"
