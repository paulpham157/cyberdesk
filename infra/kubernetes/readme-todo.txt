
If we end up using this:
az aks enable-addons --addons http_application_routing --name aks-p-scu-kubevirt --resource-group rg-p-scu-kubevirt 
To disable:
az aks disable-addons --addons http_application_routing --name aks-p-scu-kubevirt --resource-group rg-p-scu-kubevirt --no-wait 

Add azure-snapshot-class.yaml directions (near beginning), specify this is important for using Kubevirt's Clone API

Add golden snapshot directions