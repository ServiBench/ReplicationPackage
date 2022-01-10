using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using MatrixMul.Core;
using MatrixMul.Core.Model;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;

namespace MatrixMul.Azure
{
    public static class Functions
    {
        [FunctionName("OrchestrateMatrixMultiplication")]
        public static async Task<Report> OrchestrateMultiplication(
            [OrchestrationTrigger] DurableOrchestrationContext context
        )
        {
            var startTime = Util.GetUnixTimestamp();
            var calcConfig = context.GetInput<CalculationConfiguration>();
            var s = calcConfig.MatrixSize;

            var workerCount = 0;

            var calculation = await context.CallActivityAsync<MatrixCalculation>("GenerateMatrix", calcConfig);

            Matrix result = null;

            if (s < 10)
            {
                workerCount = 0;
                result = await context.CallActivityAsync<Matrix>("SerialMultiply", calculation);
            }
            else
            {
                workerCount = 5;
                var tasks = await context.CallActivityAsync<Dictionary<int, ComputationTask[]>>("DistributeWork",
                    new WorkDistributionContext
                    {
                        Calculation = calculation,
                        WorkerCount = workerCount
                    });

                var scheduledTasks = new Dictionary<int, Task<ComputationResult[]>>();
                foreach (var keyValuePair in tasks)
                {
                    scheduledTasks.Add(keyValuePair.Key, context.CallActivityAsync<ComputationResult[]>(
                        "ParallelMultiply", new ParallelWorkerContext
                        {
                            Calculation = calculation,
                            WorkerID = keyValuePair.Key,
                            Tasks = keyValuePair.Value
                        }));
                }

                var resultSet = new Dictionary<int, ComputationResult[]>();
                foreach (var keyValuePair in scheduledTasks)
                {
                    var results = await keyValuePair.Value;
                    resultSet.Add(keyValuePair.Key, results);
                }

                result = await context.CallActivityAsync<Matrix>("BuildResult", new BuildResultContext
                {
                    Calculation = calculation,
                    Results = resultSet
                });
            }

            var report = await context.CallActivityAsync<Report>("BuildReport", new ReportContext
            {
                Calculation = calculation,
                Result = result,
                StartTime = startTime,
                CallbackURL = calcConfig.DoCallback ? calcConfig.CallbackURL : null,
                WorkerCount = workerCount
            });

            return report;
        }

        [FunctionName("GenerateMatrix")]
        public static MatrixCalculation GenerateMatrix([ActivityTrigger] CalculationConfiguration cfg, ILogger log)
        {
            var s = cfg.MatrixSize;

            log.LogInformation($"Creating Two {s}x{s} matrices");
            var repo = new InMemoryMatrixMulRepository();
            var hndlr = new FunctionHandler(repo);
            var id = hndlr.CreateMatrix(s, cfg.MaxValue, cfg.Seed);

            log.LogInformation($"Created MatrixCalculations with ID {id}");

            return repo.GetCalculation(id);
        }

        [FunctionName("SerialMultiply")]
        public static Matrix SerialMultiply([ActivityTrigger] MatrixCalculation calculation, ILogger log)
        {
            var repo = new InMemoryMatrixMulRepository();
            repo.StoreCalculation("an_id", calculation);
            var hndlr = new FunctionHandler(repo);

            log.LogInformation("Serially multiplying two matrices");
            hndlr.SerialMultiply("an_id");

            return repo.GetResultMatrix("an_id");
        }

        [FunctionName("DistributeWork")]
        public static Dictionary<int, ComputationTask[]> DistributeWork([ActivityTrigger] WorkDistributionContext ctx,
            ILogger log)
        {
            var repo = new InMemoryMatrixMulRepository();
            repo.StoreCalculation("an_id", ctx.Calculation);
            var hndlr = new FunctionHandler(repo);

            log.LogInformation("Scheduling Tasks");
            hndlr.ScheduleMultiplicationTasks("an_id", ctx.WorkerCount);

            return repo.Tasks["an_id"];
        }

        [FunctionName("ParallelMultiply")]
        public static ComputationResult[] ParallelMultiply([ActivityTrigger] ParallelWorkerContext ctx, ILogger log)
        {
            var repo = new InMemoryMatrixMulRepository();
            repo.StoreCalculation("an_id", ctx.Calculation);
            repo.StoreComputationTasksForWorker("an_id", ctx.WorkerID, ctx.Tasks);
            var hndlr = new FunctionHandler(repo);

            log.LogInformation($"Worker #{ctx.WorkerID} Running parallel Multiplication tasks");
            hndlr.ParallelMultiplyWorker("an_id", ctx.WorkerID);

            return repo.GetComputationResults("an_id", ctx.WorkerID);
        }


        [FunctionName("BuildResult")]
        public static Matrix BuildResultMatrix([ActivityTrigger] BuildResultContext ctx, ILogger log)
        {
            var repo = new InMemoryMatrixMulRepository();
            repo.StoreCalculation("an_id", ctx.Calculation);
            repo.WorkerResults.Add("an_id", ctx.Results);
            var hndlr = new FunctionHandler(repo);

            log.LogInformation($"Building Result Matrix");
            hndlr.BuildResultMatrix("an_id", ctx.Results.Count);

            return repo.GetResultMatrix("an_id");
        }

        [FunctionName("BuildReport")]
        public static Report BuildReport([ActivityTrigger] ReportContext ctx, ILogger log)
        {
            var repo = new InMemoryMatrixMulRepository();
            repo.StoreCalculation("an_id", ctx.Calculation);
            repo.StoreResultMatrix("an_id", ctx.Result);
            var hndlr = new FunctionHandler(repo);

            log.LogInformation($"Building Report");
            return hndlr.GenerateReport(ctx.CallbackURL, ctx.StartTime, "an_id", ctx.WorkerCount);
        }

        [FunctionName("TriggerMatrixMultiplication")]
        public static async Task<HttpResponseMessage> StartMultiplication(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get")]
            HttpRequestMessage msg,
            HttpRequest req,
            [OrchestrationClient] DurableOrchestrationClient starter,
            ILogger log)
        {
            var matrixSize = 125;
            var maxValue = 5000;
            if (req.Query.ContainsKey("size"))
            {
                try
                {
                    matrixSize = int.Parse(req.Query["size"]);
                }
                catch (Exception)
                {
                }
            }

            if (req.Query.ContainsKey("max"))
            {
                try
                {
                    maxValue = int.Parse(req.Query["max"]);
                }
                catch (Exception)
                {
                }
            }

            var hasCallback = req.Query.ContainsKey("callback");
            var callback = "";
            if (hasCallback)
            {
                callback = req.Query["callback"];
            }

            long seed = -1;
            if (req.Query.ContainsKey("seed"))
            {
                if (!long.TryParse(req.Query["seed"], out seed))
                {
                    seed = -1;
                }
            }


            // Function input comes from the request content.
            string instanceId = await starter.StartNewAsync("OrchestrateMatrixMultiplication",
                new CalculationConfiguration
                {
                    MaxValue = maxValue,
                    MatrixSize = matrixSize,
                    DoCallback = hasCallback,
                    CallbackURL = callback,
                    Seed = (int) seed,
                });

            log.LogInformation($"Started orchestration with ID = '{instanceId}' with Matrix Size n={matrixSize}.");

            return starter.CreateCheckStatusResponse(msg, instanceId);
        }
    }

    public class CalculationConfiguration
    {
        public int MatrixSize { get; set; }
        public int MaxValue { get; set; }
        public bool DoCallback { get; set; }
        public int Seed { get; set; }
        public string CallbackURL { get; set; }
    }

    public class WorkDistributionContext
    {
        public MatrixCalculation Calculation { get; set; }
        public int WorkerCount { get; set; }
    }

    public class ReportContext
    {
        public MatrixCalculation Calculation { get; set; }
        public Matrix Result { get; set; }
        public int WorkerCount { get; set; }
        public long StartTime { get; set; }
        public string CallbackURL { get; set; }
    }

    public class ParallelWorkerContext
    {
        public MatrixCalculation Calculation { get; set; }
        public ComputationTask[] Tasks { get; set; }
        public int WorkerID { get; set; }
    }

    public class BuildResultContext
    {
        public MatrixCalculation Calculation { get; set; }
        public Dictionary<int, ComputationResult[]> Results { get; set; }
    }
}