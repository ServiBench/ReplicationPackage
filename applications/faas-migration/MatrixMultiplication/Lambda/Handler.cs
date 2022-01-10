using System;
using System.Runtime.Serialization;
using Amazon;
using Amazon.Lambda.Core;
using Amazon.Lambda.Serialization.Json;
using Amazon.S3;
using Amazon.S3.Transfer;
using MatrixMul.Core;
using MatrixMul.Core.Interfaces;
using MatrixMul.Core.Model;
using Amazon.XRay.Recorder.Handlers.AwsSdk;

[assembly: LambdaSerializer(typeof(JsonSerializer))]

namespace MatrixMul.Lambda
{
    public class Handler
    {
        private string bucketName;
        private readonly string region;
        private readonly IAmazonS3 s3Client;
        private JsonSerializer serializer;
        private TransferUtility transferUtility;

        private IMatrixMulRepository _mulRepository;
        private FunctionHandler handler;

        public Handler()
        {
            AWSSDKHandler.RegisterXRayForAllServices();
            bucketName = Environment.GetEnvironmentVariable("DATA_BUCKET_NAME");
            region = Environment.GetEnvironmentVariable("DATA_BUCKET_REGION");
            s3Client = new AmazonS3Client(RegionEndpoint.GetBySystemName(region));
            transferUtility = new TransferUtility(s3Client);
            serializer = new JsonSerializer();

            _mulRepository = new S3MatrixMulRepository(transferUtility, serializer, bucketName);
            handler = new FunctionHandler(_mulRepository);
        }

        public FunctionContext CreateMatrix(FunctionContext ctx)
        {
            var start = Util.GetUnixTimestamp();
            if (ctx.MatrixSize == 0)
            {
                Console.WriteLine("No Size Set. Using Default Size");
                ctx.MatrixSize = 200;
            }

            if (ctx.MaxValue == 0)
            {
                Console.WriteLine("No Max Set. Using Default MaxValue");
                ctx.MaxValue = 150;
            }

            if (ctx.Seed == 0)
            {
                ctx.Seed = -1;
            }

            var id = handler.CreateMatrix(ctx.MatrixSize, ctx.MaxValue, ctx.Seed);
            var res = new FunctionContext
            {
                Start = start,
                CalculationID = id,
                MatrixSize = ctx.MatrixSize,
                MaxValue = ctx.MaxValue,
                CallbackUrl = ctx.CallbackUrl
            };

            return res;
        }

        public FunctionContext SerialMultiply(FunctionContext ctx)
        {
            handler.SerialMultiply(ctx.CalculationID);
            ctx.WorkerCount = "0";
            return ctx;
        }

        public FunctionContext ScheduleMultiplyTasks(FunctionContext ctx)
        {
            int workerCnt = int.Parse(ctx.WorkerCount);
            handler.ScheduleMultiplicationTasks(ctx.CalculationID, workerCnt);
            return ctx;
        }

        public FunctionContext MultiplyTasksWorker(FunctionContext ctx)
        {
            int workerId = int.Parse(ctx.WorkerID);
            handler.ParallelMultiplyWorker(ctx.CalculationID, workerId);
            return ctx;
        }

        public FunctionContext BuildResultMatrix(FunctionContext ctx)
        {
            int workerCnt = int.Parse(ctx.WorkerCount);
            handler.BuildResultMatrix(ctx.CalculationID, workerCnt);

            return ctx;
        }

        public Report BuildReport(FunctionContext ctx)
        {
            return handler.GenerateReport(ctx.CallbackUrl, ctx.Start, ctx.CalculationID, int.Parse(ctx.WorkerCount));
        }
    }

    [DataContract]
    public class FunctionContext
    {
        [DataMember(IsRequired = false)] public long Start { get; set; }
        [DataMember(IsRequired = false)] public string CallbackUrl { get; set; }
        [DataMember(IsRequired = false)] public int MatrixSize { get; set; }
        [DataMember(IsRequired = false)] public int MaxValue { get; set; }
        [DataMember(IsRequired = false)] public int Seed { get; set; }
        [DataMember(IsRequired = false)] public string CalculationID { get; set; }

        [DataMember(IsRequired = false)] public string WorkerID { get; set; }
        [DataMember(IsRequired = false)] public string WorkerCount { get; set; }
    }
}