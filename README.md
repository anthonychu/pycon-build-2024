

```bash
RESOURCE_GROUP=demo-may-2024
LOCATION=westus3
ENVIRONMENT_NAME=demo-may-2024
ACR_NAME=demomay2024
JOB_NAME=indexer-job
QDRANT_NAME=qdrantdb
CHATAPP_NAME=chatapp
OPENAI_NAME=openai-acapms
OPENAI_RESOURCE_GROUP_NAME=openai-demo
STORAGE_ACCOUNT_NAME=demomay2024

az group create --name $RESOURCE_GROUP --location $LOCATION

az containerapp env create --name $ENVIRONMENT_NAME --resource-group $RESOURCE_GROUP --location $LOCATION \
    --enable-dedicated-gpu

az acr create --name $ACR_NAME --resource-group $RESOURCE_GROUP --location $LOCATION --sku Standard --admin-enabled true

az acr build -r $ACR_NAME -t chatapp:1.3 .

az storage account create --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP --location $LOCATION --sku Standard_LRS

FILE_SHARE_NAME=pdfs
az storage share create --name $FILE_SHARE_NAME --account-name $STORAGE_ACCOUNT_NAME

az storage file upload --share-name $FILE_SHARE_NAME --source ./more-data/azure-container-apps.pdf --account-name $STORAGE_ACCOUNT_NAME
az storage file upload --share-name $FILE_SHARE_NAME --source ./more-data/azure-azure-functions.pdf --account-name $STORAGE_ACCOUNT_NAME

STORAGE_KEY=`az storage account keys list --account-name $STORAGE_ACCOUNT_NAME --query "[0].value" -o tsv`

az containerapp env storage set --name $ENVIRONMENT_NAME --resource-group $RESOURCE_GROUP \
    --storage-name $STORAGE_ACCOUNT_NAME --access-mode ReadOnly --azure-file-account-key $STORAGE_KEY \
    --azure-file-account-name $STORAGE_ACCOUNT_NAME --azure-file-share-name $FILE_SHARE_NAME

az containerapp job create --name $JOB_NAME --resource-group $RESOURCE_GROUP \
    --image $ACR_NAME.azurecr.io/chatapp:1.3 --environment $ENVIRONMENT_NAME \
    --cpu 2 --memory 4 \
    --registry-server $ACR_NAME.azurecr.io \
    --trigger-type manual \
    --env-vars "QDRANT_HOST=qdrantdb" "QDRANT_PORT=6333" \
    --args "indexer_job"

az containerapp job update --name $JOB_NAME --resource-group $RESOURCE_GROUP --yaml ./indexer-job.yaml

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

OPENAI_ENDPOINT=`az cognitiveservices account show --name $OPENAI_NAME --resource-group $OPENAI_RESOURCE_GROUP_NAME --query properties.endpoint -o tsv`

OPENAI_RESOURCE_ID=`az cognitiveservices account show --name $OPENAI_NAME --resource-group $OPENAI_RESOURCE_GROUP_NAME --query id -o tsv`


az containerapp create --name $CHATAPP_NAME --resource-group $RESOURCE_GROUP \
    --image $ACR_NAME.azurecr.io/chatapp:1.3 --environment $ENVIRONMENT_NAME \
    --cpu 2 --memory 4 \
    --registry-server $ACR_NAME.azurecr.io \
    --env-vars "QDRANT_HOST=qdrantdb" "QDRANT_PORT=6333" "AZURE_OPENAI_ENDPOINT=https://$OPENAI_NAME.openai.azure.com/" \
    --args "chat_app" \
    --ingress external --target-port 8000 --system-assigned \
    --min-replicas 1 --max-replicas 1

CONTAINER_APP_MI_ID=`az containerapp show --name $CHATAPP_NAME --resource-group $RESOURCE_GROUP --query identity.principalId -o tsv`

# assign "Cognitive Services OpenAI User" role to container app identity
az role assignment create --role "Cognitive Services OpenAI User" --assignee $CONTAINER_APP_MI_ID --scope $OPENAI_RESOURCE_ID

```