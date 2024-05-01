

```bash
RESOURCE_GROUP=demo-may-2024
LOCATION=westus3
ENVIRONMENT_NAME=demo-may-2024
ACR_NAME=demomay2024
JOB_NAME=indexer-job
QDRANT_NAME=qdrantdb

az group create --name $RESOURCE_GROUP --location $LOCATION

az containerapp env create --name $ENVIRONMENT_NAME --resource-group $RESOURCE_GROUP --location $LOCATION \
    --enable-dedicated-gpu

az acr create --name $ACR_NAME --resource-group $RESOURCE_GROUP --location $LOCATION --sku Standard --admin-enabled true

az acr build -r $ACR_NAME -t chatapp:1.1 -f Dockerfile.job .

az containerapp job create --name $JOB_NAME --resource-group $RESOURCE_GROUP \
    --image $ACR_NAME.azurecr.io/chatapp:1.1 --environment $ENVIRONMENT_NAME \
    --cpu 2 --memory 4 \
    --registry-server $ACR_NAME.azurecr.io \
    --trigger-type manual \
    --env-vars "QDRANT_HOST=qdrantdb" "QDRANT_PORT=6333"

az containerapp job start --name $JOB_NAME --resource-group $RESOURCE_GROUP

az containerapp add-on qdrant create \
    --environment $ENVIRONMENT_NAME \
    --resource-group $RESOURCE_GROUP \
    --name $QDRANT_NAME

az containerapp update  \
    --resource-group $RESOURCE_GROUP \
    --name $QDRANT_NAME \
    --min-replicas 1 \
    --max-replicas 1
```