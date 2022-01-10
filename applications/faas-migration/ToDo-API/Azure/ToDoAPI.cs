using System;
using Microsoft.WindowsAzure.Storage.Table;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Web.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

namespace AzureToDo
{
    public static class ToDoAPI
    {
        [FunctionName("put")]
        [StorageAccount("AzureWebJobsStorage")]
        public static async Task<IActionResult> AddItem(
            [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = null)]
            HttpRequest req,
            [Table("todo")] CloudTable table, ILogger log)
        {
            try
            {
                using (var reader = new StreamReader(req.Body))
                {
                    var item = JsonConvert.DeserializeObject<ToDoItem>(reader.ReadToEnd());
                    var uid = Guid.NewGuid().ToString();
                    item.ID = uid;
                    item.PartitionKey = "http";
                    item.InsertionTimestamp = (long) DateTime.UtcNow.Subtract(new DateTime(1970, 1, 1)).TotalSeconds;
                    item.DoneTimestamp = -1;

                    log.LogInformation($"Inserted ToDo Message with UID {item.ID}");

                    var batch = new TableBatchOperation();
                    batch.Insert(item);

                    await table.ExecuteBatchAsync(batch);

                    return new OkObjectResult(item.ToToDoDTO());
                }
            }
            catch (Exception e)
            {
                log.LogError("Adding Item has failed", e);
                return new InternalServerErrorResult();
            }
        }

        [FunctionName("del")]
        [StorageAccount("AzureWebJobsStorage")]
        public static async Task<IActionResult> DeleteItem(
            [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = null)]
            HttpRequest req,
            ILogger log,
            [Table("todo")] CloudTable todoTable)
        {
            if (!req.Query.ContainsKey("id"))
            {
                return new BadRequestResult();
            }

            string uid = req.Query["id"];
            Guid uuid;
            if (!Guid.TryParse(uid, out uuid))
            {
                return new NotFoundResult();
            }

            log.LogInformation($"Attempting to Delete {uid}");

            try
            {
                var batch = new TableBatchOperation();
                batch.Delete(new ToDoItem
                {
                    ID = uid,
                    ETag = "*"
                });

                await todoTable.ExecuteBatchAsync(batch);

                return new OkObjectResult($"Removed {uid}");
            }
            catch (Exception e)
            {
                // Return 404 if process fails since most of the cases fail due to invalid IDs
                log.LogCritical(e, "Deletion Failed");
                return new NotFoundResult();
            }
        }

        [FunctionName("lst")]
        [StorageAccount("AzureWebJobsStorage")]
        public static async Task<IActionResult> ListItems(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = null)]
            HttpRequest req,
            [Table("todo")] CloudTable todoTable,
            ILogger log)
        {
            var query = new TableQuery<ToDoItem>().Where(TableQuery.GenerateFilterCondition("PartitionKey",
                QueryComparisons.Equal,
                "http"));

            var result = await todoTable.ExecuteQuerySegmentedAsync(query, null);

            return new OkObjectResult(result.Results.Select(e => e.ToToDoDTO()).ToArray());
        }

        [FunctionName("get")]
        [StorageAccount("AzureWebJobsStorage")]
        public static async Task<IActionResult> GetItem(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = null)]
            HttpRequest req,
            [Table("todo")] CloudTable todoTable,
            ILogger log)
        {
            if (!req.Query.ContainsKey("id"))
            {
                return new BadRequestResult();
            }

            string uid = req.Query["id"];
            Guid uuid;
            if (!Guid.TryParse(uid, out uuid))
            {
                return new NotFoundResult();
            }

            try
            {
                var query = new TableQuery<ToDoItem>().Where(
                    TableQuery.GenerateFilterCondition("RowKey", QueryComparisons.Equal, uid)
                );

                var result = await todoTable.ExecuteQuerySegmentedAsync(query, null);

                return new OkObjectResult(result.Results.Select(e => e.ToToDoDTO()).First());
            }
            catch (Exception e)
            {
                // Return 404 if process fails since most of the cases fail due to invalid IDs
                log.LogCritical(e, "Get Failed");
                return new NotFoundResult();
            }
        }

        [FunctionName("done")]
        [StorageAccount("AzureWebJobsStorage")]
        public static async Task<IActionResult> MarkAsDone(
            [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = null)]
            HttpRequest req,
            [Table("todo")] CloudTable todoTable,
            ILogger log)
        {
            if (!req.Query.ContainsKey("id"))
            {
                return new BadRequestResult();
            }

            string uid = req.Query["id"];
            Guid uuid;
            if (!Guid.TryParse(uid, out uuid))
            {
                return new NotFoundResult();
            }

            try
            {
                var query = new TableQuery<ToDoItem>().Where(
                    TableQuery.GenerateFilterCondition("RowKey", QueryComparisons.Equal, uid)
                );

                var result = await todoTable.ExecuteQuerySegmentedAsync(query, null);

                var elem = result.First();
                elem.Done = true;
                elem.DoneTimestamp = (long) DateTime.UtcNow.Subtract(new DateTime(1970, 1, 1)).TotalSeconds;

                var batch = new TableBatchOperation();
                batch.Replace(elem);
                await todoTable.ExecuteBatchAsync(batch);

                return new OkObjectResult(elem.ToToDoDTO());
            }
            catch (Exception e)
            {
                // Return 404 if process fails since most of the cases fail due to invalid IDs
                log.LogCritical(e, "Delete Failed");
                return new NotFoundResult();
            }
        }
    }

    public class ToDoItem : TableEntity
    {
        public ToDoItem()
        {
            this.PartitionKey = "http";
        }

        public string ID
        {
            get => RowKey;
            set => RowKey = value;
        }

        public string Title { get; set; }
        public string Description { get; set; }
        public long InsertionTimestamp { get; set; }
        public long DoneTimestamp { get; set; }
        public bool Done { get; set; }

        public ToDoDTO ToToDoDTO()
        {
            return new ToDoDTO
            {
                ID = ID,
                Title = Title,
                Description = Description,
                InsertionTimestamp = InsertionTimestamp,
                Done = Done,
                DoneTimestamp = DoneTimestamp,
            };
        }
    }

    public class ToDoDTO
    {
        [JsonProperty("ID")] public string ID { get; set; }
        [JsonProperty("title")] public string Title { get; set; }
        [JsonProperty("description")] public string Description { get; set; }
        [JsonProperty("insertion_timestamp")] public long InsertionTimestamp { get; set; }
        [JsonProperty("done_timestamp")] public long DoneTimestamp { get; set; }
        [JsonProperty("done")] public bool Done { get; set; }
    }
}