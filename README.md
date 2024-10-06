# Introduction
This is a chat application that interacts with an API.  The API interacts with Open AI and determines what Functions to call based on the question users ask.   

Currently the functions are as follows:
- Get Weather
- Get Stock Quote
- Get Stock Technical Indicators
- Get Stock News
- Get Stock Financials

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