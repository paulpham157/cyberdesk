kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.1/deploy/static/provider/cloud/deploy.yaml 


az aks enable-addons --addons http_application_routing --name aks-p-scu-kubevirt --resource-group rg-p-scu-kubevirt 

To disable:
az aks disable-addons --addons http_application_routing --name aks-p-scu-kubevirt --resource-group rg-p-scu-kubevirt --no-wait 



gateway-deploy.yaml

