#!/bin/bash

set -eou pipefail

POD_ID=$(kubectl get pods -lapp="$PROJECT" | grep Running | awk '{print $1}')
kubectl exec -ti "$POD_ID" -- ./src/manage.py "$@"
