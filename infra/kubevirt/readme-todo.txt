
If we end up using this:
az aks enable-addons --addons http_application_routing --name aks-p-scu-kubevirt --resource-group rg-p-scu-kubevirt 
To disable:
az aks disable-addons --addons http_application_routing --name aks-p-scu-kubevirt --resource-group rg-p-scu-kubevirt --no-wait 

For now, external service for gateway service. Anything need to handle manually?
gateway-deploy.yaml

Maybe add notes for after starting a VM, you can go to the url http://<external-ip>/vnc/<vm-id>

