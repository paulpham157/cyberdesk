
If we end up using this:
az aks enable-addons --addons http_application_routing --name aks-p-scu-kubevirt --resource-group rg-p-scu-kubevirt 
To disable:
az aks disable-addons --addons http_application_routing --name aks-p-scu-kubevirt --resource-group rg-p-scu-kubevirt --no-wait 

Add docker build stuff for gateway: docker build -t "cyberdesk/gateway:v0.1.6" . and also docker push 