# Azure Functions Dataset on Github:
# https://github.com/Azure/AzurePublicDataset/blob/master/AzureFunctionsDataset2019.md
# Direct download link:
# https://azurecloudpublicdataset2.blob.core.windows.net/azurepublicdatasetv2/azurefunctions_dataset2019/azurefunctions-dataset2019.tar.xz

dataFile1 <- '../data/invocations_per_function_md.anon.d01.csv'
if (file.exists(dataFile1)) {
  print("Successfully detected dataset in data directory.")
} else {
  print("Failed to locate Azure Function Traces dataset.
        Please download and decompress the dataset from:
        https://github.com/Azure/AzurePublicDataset/blob/master/AzureFunctionsDataset2019.md
        Direct download URL (2022-01-10):
        https://azurecloudpublicdataset2.blob.core.windows.net/azurepublicdatasetv2/azurefunctions_dataset2019/azurefunctions-dataset2019.tar.xz
        For example: `data/invocations_per_function_md.anon.d01.csv`
        ")
}
