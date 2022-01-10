FROM maven:3.6.3-jdk-8-slim

ENV FUNCTIONS_CORE_TOOLS_TELEMETRY_OPTOUT=true
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
# Fix issue "Couldn't find a valid ICU package installed on the system."
# https://github.com/dotnet/core/issues/2186#issuecomment-671105420
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1


# Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-apt#install-with-one-command
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install Azure Function Tools: https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=linux%2Ccsharp%2Cbash
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg && \
    mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg && \
    echo "deb [arch=amd64] https://packages.microsoft.com/debian/$(lsb_release -rs | cut -d'.' -f 1)/prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list && \
    apt-get update && \
    apt-get install azure-functions-core-tools-3

# Install .NET core: https://docs.microsoft.com/en-us/dotnet/core/install/linux-debian
RUN curl https://packages.microsoft.com/config/debian/10/packages-microsoft-prod.deb -J -o packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y apt-transport-https && \
    apt-get update && \
    apt-get install -y dotnet-sdk-2.1

# Install Azure function extensions
COPY extensions.csproj .
RUN func extensions install

# Caching Maven dependencies and building the app could
# speedup subsequent builds

# # Cache Maven dependencies
# COPY pom.xml .
# RUN mvn dependency:resolve

# # Build app
# COPY . .
# RUN TODO(define envs here, needs build args for configurability) mvn clean install
