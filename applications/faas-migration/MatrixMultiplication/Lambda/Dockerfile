# Tags: https://hub.docker.com/_/microsoft-dotnet-sdk?tab=description
FROM mcr.microsoft.com/dotnet/sdk:5.0.103-focal-amd64

RUN apt-get update && apt-get -y install zip
RUN dotnet tool install -g Amazon.Lambda.tools
