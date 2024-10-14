# Introduction
This is a chat application that interacts with an API.  The API interacts with Open AI and determines what Functions to call based on the question users ask.   

Currently the functions are as follows:
   
   ```
   - Get Weather - Get's the weather for city, state, country
   - Get Stock Quote - Get's the current stock price
   - Get Stock Technical Indicators - Get's the technical indicators for a stock and calculates them over a 6 month history
   - Get Stock News - Get's financial news for a stock symbol
   - Get Stock Financials - Get's the financial results (10K/10Q) for a stock symbol
   - Get Option Chains - Get's option chains (Calls & Puts) that are not in the money for a stock symbol
   - Python Code Execution - The ability to run  python code with the ability to do charting
   ```

# Getting Started
1. Download the repo locally:
    ```
    git clone https://github.com/philnandreoli/langchain-financial-advisor.git
    ```

2. Create a `.env` file in the root project directory and add the following:

   ```
    AZURE_OPENAI_API_KEY=               # Retrieve this from your Azure Portal Deployment
    AZURE_OPENAI_ENDPOINT=              # Retrieve this from your Azure Portal Deployment
    AZURE_OPENAI_MODEL=                 # Retrieve this from your Azure Portal Deployment
    OPENAI_API_VERSION=                 # Retrieve this from your Azure Portal Deployment
    POLYGON_API_KEY=                    # Get one here: https://www.polygon.io
    POLYGON_API_ENDPOINT=               # Get one here: https://www.polygon.io
    OPENWEATHER_API_KEY=                # Get one here: https://www.openweather.org
    PORT=                               # Choose a port number you want the API to run on
    CHAT_PORT=8501
    API_ENDPOINT=                       http://langchain-financial-reporting-api:${PORT}/financials
    APPLICATIONINSIGHTS_CONNECTION_STRING = # Retrieve this from your Azure Portal Deployment
    # When using Azure Container Apps Dynamic Session Pools Endpoint you need have a Service Principal created. 
    # Once the service principle has been created you need to assign it specifc roles. 
    # You can read about it here: https://learn.microsoft.com/en-us/azure/container-apps/sessions?tabs=azure-cli#authentication
    POOL_MANAGEMENT_ENDPOINT            # Azure Container Apps Dynamic Session Pools Endpoint
    AZURE_CLIENT_ID=                    # Service Principal Client ID
    AZURE_TENANT_ID=                    # Tentant ID where the service principal is
    AZURE_CLIENT_SECRET=                # Client Secret for the service Principal
   ```

# Run the agent
We recommend using Docker to run this application locally.   

You can find Docker installation instructions [here][1].

Once installed, rn the following command in the root project directory to start the application: 
   ```
    docker-compose up 
   ```

# Open the Browser
   ```
    http://localhost:8501/
   ```

# 🛑 DISCLAIMER 🛑
This application is demo and any trades you make on your own is done at your own risk.  Please do your own research prior to making any trade. 

# License
This project is licensed under the MIT License


[1]:<https://docs.docker.com/get-docker/>
[2]:<https://www.polygon.io>
[3]:<https://www.openweather.org>
[4]:<https://learn.microsoft.com/en-us/azure/container-apps/sessions?tabs=azure-cli#authentication>