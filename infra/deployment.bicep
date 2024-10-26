param adminPrincipalId string = '06d01fe2-4ae1-4470-b3ec-d658a60df23c'
param openAiModelDeploymentLocation string = 'eastus2'

@description('The name of the Open AI Model that is goingt to be used')
@allowed([
  'gpt-4o'
  'gpt-01'
])
param openAiModelDeploymentName string = 'gpt-4o'

@description('The OpenWeather API Key that you have when received when you signed up for the service')
param OpenWeatherApiKey string

@description('The endpoint for the Polygon API')
param polygonApiEndpoint string 

@description('The API Key for the Polygon API that you have when you signed up for the service')
param polygonApiKey string

@description('The Client ID from Entra used for Authentication with the API')
param apiAppClientId string

@description('The Client ID from Open API used for Authentication with the API')
param apiOpenApiClientId string

@description('The version of the container image that is going to be used during the deployment.   During the CI/CD pipeline, this value will be replaced with the version of the image that was built')
param containerVersion string

@description('The endpoint for the container registry')
param containerRegistryEndpoint string

@description('The resource group where the container registry is deployed')
param containerRegistryResourceGroup string

@description('The tenant where the streamlit appliction id is deployed')
param streamlitTenantId string

@description('')
param streamlitAuthorizeEndpoint string

param streamlitTokenEndpoint string 

param streamlitAppClientId string

@secure()
@description('The client secret for the streamlit application')
param streamlitAppClientSecret string

param iconUrl string


var deploymentShortString = 'finadvisor'
var uniqueResourceGroupString = substring(uniqueString(resourceGroup().id),0, 6)

//Get the role definition for the Azure Key Vault Administrator Role
resource keyVaultAdministratratorRoleDefinition 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  scope: subscription()
  name: '00482a5a-887f-4fb3-b363-3b7fe8e74483'
}

resource keyVaultSecretUserRoleDefinition 'Microsoft.Authorization/roleDefinitions@2022-05-01-preview' existing = {
  scope: subscription()
  name: '4633458b-17de-408a-b874-0445c86b69e6'
}

resource containerAppsSessionExecutorRoleDefinition 'Microsoft.Authorization/roleDefinitions@2022-05-01-preview' existing = {
  scope: subscription()
  name: '0fb8eba5-a2bb-4abe-b1c1-49dfad359bb0'
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: containerRegistryEndpoint
  scope: resourceGroup(containerRegistryResourceGroup)
}

//Create the key vault resource
resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' = {
  name: '${deploymentShortString}-kv-${uniqueResourceGroupString}'
  location: resourceGroup().location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enabledForTemplateDeployment: true
    publicNetworkAccess: 'Enabled'
    enableRbacAuthorization: true
  }
}

//Assign admin principal to be the key vault administrator
resource keyVaultAdminRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, adminPrincipalId, keyVaultAdministratratorRoleDefinition.id )
  scope: keyVault
  properties: {
    roleDefinitionId: keyVaultAdministratratorRoleDefinition.id
    principalId: adminPrincipalId
    principalType: 'User'
  }
}

//Open AI Account
resource openAiAccount 'Microsoft.CognitiveServices/accounts@2024-06-01-preview' = {
  name: '${deploymentShortString}-oaiaccount-${uniqueResourceGroupString}'
  location: openAiModelDeploymentLocation
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: '${deploymentShortString}-oaiaccount-${uniqueResourceGroupString}'
    networkAcls: {
      defaultAction: 'Allow'
    }
    publicNetworkAccess: 'Enabled'
  }
}

  //Open AI Deployment
resource openAiModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-06-01-preview' = {
    name: openAiModelDeploymentName
    parent: openAiAccount
    dependsOn: []
    sku: {
      name: 'GlobalStandard'
      capacity: 250
    }
    properties: {
      model: {
        format: 'OpenAI'
        name: openAiModelDeploymentName
        version: '2024-08-06'
      }
      versionUpgradeOption: 'OnceCurrentVersionExpired'
      raiPolicyName: 'Microsoft.Default'
  }
}

//Add a secret to the key vault for the Open AI Account endpoint
resource openAiEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2022-07-01' = {
  name: 'AZURE-OPENAI-ENDPOINT'
  parent: keyVault
  properties: {
     value: openAiAccount.properties.endpoint
  }
}

//Add a secret to the key vault for the Open AI Account Endpoint Key
resource openAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2022-07-01' = {
  name: 'AZURE-OPENAI-API-KEY'
  parent: keyVault
  properties: {
     value: openAiAccount.listKeys().key1
  }
}
//Add a scret to the key vault for the name of the Open AI Model
resource openAiModelSecret 'Microsoft.KeyVault/vaults/secrets@2022-07-01' = {
  name: 'AZURE-OPENAI-MODEL'
  parent: keyVault
  properties: {
    value: openAiModelDeployment.properties.model.name
  }
}

resource openAiModelVersionSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'OPENAI-API-VERSION'
  parent: keyVault
  properties: {
    value: openAiModelDeployment.properties.model.version
  }
}

resource openWeatherApiKeySecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'OPENWEATHER-API-KEY'
  parent: keyVault
  properties: {
    value: OpenWeatherApiKey
  }
}

resource polygonApiEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'POLYGON-API-ENDPOINT'
  parent: keyVault
  properties: {
    value: polygonApiEndpoint
  }
}

resource polygonApiKeySecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'POLYGON-API-KEY'
  parent: keyVault
  properties: {
    value: polygonApiKey
  }
}

resource apiAppClientIdSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'APP-CLIENT-ID'
  parent: keyVault
  properties: {
    value: apiAppClientId
  }
}

resource openApiAppClientIdSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'OPENAPI-CLIENT-ID'
  parent: keyVault
  properties: {
    value: apiOpenApiClientId
  }
}

resource streamlitAppTenantIdSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'STREAMLIT-APP-TENANT-ID'
  parent: keyVault
  properties: {
    value: streamlitTenantId
  }
}

resource streamlitAppAuthorizeEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'STREAMLIT-AUTHORIZE-ENDPOINT'
  parent: keyVault
  properties: {
    value: streamlitAuthorizeEndpoint
  }
}

resource streamlitTokenEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'STREAMLIT-TOKEN-ENDPOINT'
  parent: keyVault
  properties: {
    value: streamlitTokenEndpoint
  }
}

resource streamlitAppClientIdSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'STREAMLIT-APP-CLIENT-ID'
  parent: keyVault
  properties: {
    value: streamlitAppClientId
  }
}

resource streamlitAppClientSecretSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'STREAMLIT-APP-CLIENT-SECRET'
  parent: keyVault
  properties: {
    value: streamlitAppClientSecret
  }
}


resource streamlitIconUrlSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'STREAMLIT-ICON-URL'
  parent: keyVault
  properties: {
    value: iconUrl
  }
}

//Create a log analytics workspace
resource logAnalyticsWSEastUS 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${deploymentShortString}-loganalytics-${uniqueResourceGroupString}'
  location: resourceGroup().location
  properties: {
    retentionInDays: 90
  }
}

//Create an application insights resource
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${deploymentShortString}-appinsights-${uniqueResourceGroupString}'
  location: resourceGroup().location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Flow_Type: 'Bluefield'
    Request_Source: 'IbizaAIExtension'
    RetentionInDays: 90
    WorkspaceResourceId: logAnalyticsWSEastUS.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

//Add a secret to the key vault for the Application Insights Connection String
resource applicationInsightsConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'APPLICATIONINSIGHTS-CONNECTION-STRING'
  parent: keyVault
  properties: {
    value: applicationInsights.properties.ConnectionString
  }
}

resource containerAppsManagedEnvironments 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${deploymentShortString}-caenv-${uniqueResourceGroupString}'
  location: resourceGroup().location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWSEastUS.properties.customerId
        sharedKey: logAnalyticsWSEastUS.listKeys().primarySharedKey
      }
    }
    zoneRedundant: false
  }
}

resource containerAppsSessionPools 'Microsoft.App/sessionPools@2024-02-02-preview' = {
  name: '${deploymentShortString}-casp-${uniqueResourceGroupString}'
  location: resourceGroup().location
  properties: {
    poolManagementType: 'Dynamic'
    scaleConfiguration: {
      maxConcurrentSessions: 5
      readySessionInstances: 0
    }
    dynamicPoolConfiguration: {
      cooldownPeriodInSeconds: 300
    }
    containerType: 'PythonLTS'
    environmentId: containerAppsManagedEnvironments.id
    sessionNetworkConfiguration: {
      status: 'EgressEnabled'
    }
  }
}

resource poolManagementEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'POOL-MANAGEMENT-ENDPOINT'
  parent: keyVault
  properties: {
    value: containerAppsSessionPools.properties.poolManagementEndpoint
  }
}

resource corsUrlSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'CORS-URL'
  parent: keyVault
  properties: {
    value: 'https://${deploymentShortString}-ca-backend-${uniqueResourceGroupString}.${resourceGroup().location}.azurecontainerapps.io'
  }
}

resource containerApps  'Microsoft.App/containerApps@2024-03-01' = {
  name: '${deploymentShortString}-ca-backend-${uniqueResourceGroupString}'
  location: resourceGroup().location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsManagedEnvironments.id
    environmentId: containerAppsManagedEnvironments.id
    configuration: {
      secrets: [
        {
          name: 'openapi-client-id'
          keyVaultUrl: openApiAppClientIdSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'polygon-api-key'
          keyVaultUrl: polygonApiKeySecret.properties.secretUri
          identity: 'system'
        }
        {
            name: 'azure-openai-api-key'
            keyVaultUrl: openAiKeySecret.properties.secretUri
            identity: 'system'
        }
        {
            name: 'azure-openai-endpoint'
            keyVaultUrl: openAiEndpointSecret.properties.secretUri
            identity: 'system'
        }
        {
            name: 'openai-api-version'
            keyVaultUrl: openAiModelVersionSecret.properties.secretUri
            identity: 'system'
        }
        {
            name: 'cors-url'
            keyVaultUrl: corsUrlSecret.properties.secretUri
            identity: 'system'
        }
        {
            name: 'openweather-api-key'
            keyVaultUrl: openWeatherApiKeySecret.properties.secretUri
            identity: 'system'
        }
        {
            name: 'azure-openai-model'
            keyVaultUrl: openAiModelSecret.properties.secretUri
            identity: 'system'
        }
        {
            name: 'pool-management-endpoint'
            keyVaultUrl: poolManagementEndpointSecret.properties.secretUri
            identity: 'system'
        }
        {
            name: 'app-client-id'
            keyVaultUrl: apiAppClientIdSecret.properties.secretUri
            identity: 'system'
        }
        {
            name: 'polygon-api-endpoint'
            keyVaultUrl: polygonApiEndpointSecret.properties.secretUri
            identity: 'system'
        }
        {
            name: 'applicationinsights-connection-string'
            keyVaultUrl: applicationInsightsConnectionStringSecret.properties.secretUri
            identity: 'system'
        }
        {
          name: 'container-registry-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
      ]
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        exposedPort: 0
        transport: 'auto'
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
        allowInsecure: false
        stickySessions: {
          affinity: 'sticky'
        }
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'container-registry-password'
        }
      ]
      maxInactiveRevisions: 100
    }
    template: {
      containers: [
        {
          image: '${containerRegistry.properties.loginServer}/financial-advisor/langchain/financial-reporting-api:${containerVersion}'
          name: '${deploymentShortString}-ca-backend-${uniqueResourceGroupString}'
          env: [
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'azure-openai-api-key'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              secretRef: 'azure-openai-endpoint'
            }
            {
              name: 'AZURE_OPENAI_MODEL'
              secretRef: 'azure-openai-model'
            }
            {
              name: 'OPENAI_API_VERSION'
              secretRef: 'openai-api-version'
            }
            {
              name: 'POLYGON_API_KEY'
              secretRef: 'polygon-api-key'
            }
            {
              name: 'POLYGON_API_ENDPOINT'
              secretRef: 'polygon-api-endpoint'
            }
            {
              name: 'OPENWEATHER_API_KEY'
              secretRef: 'openweather-api-key'
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              secretRef: 'applicationinsights-connection-string'
            }
            {
              name: 'POOL_MANAGEMENT_ENDPOINT'
              secretRef: 'pool-management-endpoint'
            }
            {
              name: 'APP_CLIENT_ID'
              secretRef: 'app-client-id'
            }
            {
              name: 'OPENAPI_CLIENT_ID'
              secretRef: 'openapi-client-id'
            }
            {
              name: 'CORS_URL'
              secretRef: 'cors-url'
            }
          ]
          resources: {
            cpu: 1
            memory: '2.0Gi'
          }
          probes: []
        }
      ]
      scale:{
        minReplicas: 0
        maxReplicas: 3
      }
    }
  }
}


resource keyVaulUserSecretRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, containerApps.name, keyVaultSecretUserRoleDefinition.id)
  scope: keyVault
  properties: {
    roleDefinitionId: keyVaultSecretUserRoleDefinition.id
    principalId: containerApps.identity.principalId
    principalType: 'ServicePrincipal'
    description: '${containerApps.name} has access to the secrets in the key vault'
  }
}


resource containerAppsPermissions 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerAppsSessionPools.id, containerApps.name, containerAppsSessionExecutorRoleDefinition.id)
  scope: containerAppsSessionPools
  properties: {
    roleDefinitionId: containerAppsSessionExecutorRoleDefinition.id
    principalId: containerApps.identity.principalId
    principalType: 'ServicePrincipal'
    description: '${containerApps.name} has access to the container apps session pools'
  }
}

resource apiEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  name: 'API-ENDPOINT'
  parent: keyVault
  properties: {
    value: 'https://${containerApps.properties.latestRevisionFqdn}/v2/financials'
  }
}


resource containerAppsFrontEnd  'Microsoft.App/containerApps@2024-03-01' = {
  name: '${deploymentShortString}-ca-frontend-${uniqueResourceGroupString}'
  location: resourceGroup().location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsManagedEnvironments.id
    environmentId: containerAppsManagedEnvironments.id
    configuration: {
      secrets: [
        {
          name: 'app-tenant-id'
          keyVaultUrl: streamlitAppTenantIdSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'authorize-endpoint'
          keyVaultUrl: streamlitAppAuthorizeEndpointSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'token-endpoint'
          keyVaultUrl: streamlitTokenEndpointSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'streamlit-app-client-id'
          keyVaultUrl: streamlitAppClientIdSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'api-client-id'
          keyVaultUrl: apiAppClientIdSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'app-client-secret'
          keyVaultUrl: streamlitAppClientSecretSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'redirect-uri'
          value: 'https://${containerAppsFrontEnd.properties.latestRevisionFqdn}'
        }
        {
          name: 'icon-url'
          keyVaultUrl: streamlitIconUrlSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'api-endpoint'
          keyVaultUrl: apiEndpointSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'container-registry-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
      ]
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8501
        exposedPort: 0
        transport: 'auto'
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
        allowInsecure: false
        stickySessions: {
          affinity: 'sticky'
        }
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'container-registry-password'
        }
      ]
      maxInactiveRevisions: 100
    }
    template: {
      containers: [
        {
          image: '${containerRegistry.properties.loginServer}/financial-advisor/langchain/financial-reporting-chat:${containerVersion}'
          name: '${deploymentShortString}-ca-frontend-${uniqueResourceGroupString}'
          env: [
            {
              name: 'API_ENDPOINT'
              secretRef: 'api-endpoint'
            }
            {
              name: 'APP_TENANT_ID'
              secretRef: 'app-tenant-id'
            }
            {
              name: 'AUTHORIZE_ENDPOINT'
              secretRef: 'authorize-endpoint'
            }
            {
              name: 'TOKEN_ENDPOINT'
              secretRef: 'token-endpoint'
            }
            {
              name: 'STREMLIT_APP_CLIENT_ID'
              secretRef: 'streamlit-app-client-id'
            }
            {
              name: 'API_CLIENT_ID'
              secretRef: 'api-client-id'
            }
            {
              name: 'APP_CLIENT_SECRET'
              secretRef: 'app-client-secret'
            }
            {
              name: 'REDIRECT_URI'
              secretRef: 'redirect-uri'
            }
            {
              name: 'ICON_URL'
              secretRef: 'icon-url'
            }
          ]
          resources: {
            cpu: 1
            memory: '2.0Gi'
          }
          probes: []
        }
      ]
      scale:{
        minReplicas: 0
        maxReplicas: 3
      }
    }
  }
}

resource frontendKeyVaulUserSecretRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, containerAppsFrontEnd.name, keyVaultSecretUserRoleDefinition.id)
  scope: keyVault
  properties: {
    roleDefinitionId: keyVaultSecretUserRoleDefinition.id
    principalId: containerAppsFrontEnd.identity.principalId
    principalType: 'ServicePrincipal'
    description: '${containerAppsFrontEnd.name} has access to the secrets in the key vault'
  }
}
