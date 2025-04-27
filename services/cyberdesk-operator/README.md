Run locally:
- Ensure you are on the developer cluster
- Scale down the cluster operator deployment (notify team): kubectl scale deployment cyberdesk-operator --replicas=0 -n cyberdesk-system
- docker build -t cyberdesk/cyberdesk-operator:local .
- docker run --rm -it -v "${env:USERPROFILE}\.kube:/root/.kube:ro" --env-file ./.env cyberdesk/cyberdesk-operator:local