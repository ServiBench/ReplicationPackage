using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using MatrixMul.Core.Interfaces;
using MatrixMul.Core.Model;
using Minio;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace MatrixMul.IBMCloud
{
    public class CloudObjectStorageRepository : IMatrixMulRepository
    {
        private string _bucketName;
        private string _endpoint;
        private string _accessKey;
        private string _secretKey;

        private MinioClient _client;

        public CloudObjectStorageRepository(JObject input)
        {
            _bucketName = input["s3_bucket_name"].ToString();
            _endpoint = input["s3_endpoint"].ToString();
            _accessKey = input["s3_access_key"].ToString();
            _secretKey = input["s3_secret_key"].ToString();

            Console.WriteLine($"{_bucketName}@{_endpoint}: A: {_accessKey} S: {_secretKey}");

            _client = new MinioClient(_endpoint, _accessKey, _secretKey);

            var r = _client.BucketExistsAsync(_bucketName);
            Task.WaitAll(r);
            if (!r.Result)
            {
                Task.WaitAll(_client.MakeBucketAsync(_bucketName, ""));
            }
        }

        public CloudObjectStorageRepository(string bucketName, string endpoint, string accessKey, string secretKey)
        {
            _bucketName = bucketName;
            _endpoint = endpoint;
            _accessKey = accessKey;
            _secretKey = secretKey;

            _client = new MinioClient(_endpoint, _accessKey, _secretKey);
        }

        public void StoreCalculation(string id, MatrixCalculation calculation)
        {
            Console.WriteLine("Attempting to store config in object storage");
            var data = JsonConvert.SerializeObject(calculation);
            var ms = new MemoryStream();
            ms.Write(Encoding.UTF8.GetBytes(data));
            ms.Seek(0, SeekOrigin.Begin);
            Task.WaitAll(_client.PutObjectAsync(_bucketName, id, ms, ms.Length));
        }

        public MatrixCalculation GetCalculation(string id)
        {
            var ms = new MemoryStream();
            Task.WaitAll(_client.GetObjectAsync(_bucketName, id, (e) => e.CopyTo(ms)));

            return JsonConvert.DeserializeObject<MatrixCalculation>(Encoding.UTF8.GetString(ms.ToArray()));
        }

        public void DeleteCalculation(string id)
        {
            Task.WaitAll(_client.RemoveObjectAsync(_bucketName, id));
        }

        public void StoreResultMatrix(string id, Matrix matrix)
        {
            Console.WriteLine("Writing Result matrix");
            var data = JsonConvert.SerializeObject(matrix);
            var ms = new MemoryStream();
            ms.Write(Encoding.UTF8.GetBytes(data));
            ms.Seek(0, SeekOrigin.Begin);
            Console.WriteLine($"Sending {ms.Length} Bytes to Object Storage");
            Task.WaitAll(_client.PutObjectAsync(_bucketName, GetResultKey(id), ms, ms.Length));
        }

        public Matrix GetResultMatrix(string id)
        {
            var ms = new MemoryStream();
            Task.WaitAll(_client.GetObjectAsync(_bucketName, GetResultKey(id), (e) => e.CopyTo(ms)));

            return JsonConvert.DeserializeObject<Matrix>(Encoding.UTF8.GetString(ms.ToArray()));
        }
        
        public void DeleteResultMatrix(string id)
        {
            Task.WaitAll(_client.RemoveObjectAsync(_bucketName, GetResultKey(id)));
        }

        public void StoreComputationTasksForWorker(string id, int workerId, ComputationTask[] tasks)
        {
            var data = JsonConvert.SerializeObject(tasks);
            var ms = new MemoryStream();
            ms.Write(Encoding.UTF8.GetBytes(data));
            ms.Seek(0, SeekOrigin.Begin);
            Task.WaitAll(_client.PutObjectAsync(_bucketName, GetTaskKeyForWorker(id, workerId), ms, ms.Length));
        }

        public ComputationTask[] GetComputationTasksForWorker(string id, int workerId)
        {
            var ms = new MemoryStream();
            Task.WaitAll(_client.GetObjectAsync(_bucketName, GetTaskKeyForWorker(id, workerId), (e) => e.CopyTo(ms)));

            return JsonConvert.DeserializeObject<ComputationTask[]>(Encoding.UTF8.GetString(ms.ToArray()));
        }

        public void DeleteComputationTasks(string id, int workerId)
        {
            Task.WaitAll(_client.RemoveObjectAsync(_bucketName, GetTaskKeyForWorker(id, workerId)));
        }

        public void StoreComputationResults(string id, int workerId, ComputationResult[] results)
        {
            var data = JsonConvert.SerializeObject(results);
            var ms = new MemoryStream();
            ms.Write(Encoding.UTF8.GetBytes(data));
            ms.Seek(0, SeekOrigin.Begin);
            Task.WaitAll(_client.PutObjectAsync(_bucketName, GetResultKeyForWorker(id, workerId), ms, ms.Length));
        }

        public ComputationResult[] GetComputationResults(string id, int workerId)
        {
            var ms = new MemoryStream();
            Task.WaitAll(_client.GetObjectAsync(_bucketName, GetResultKeyForWorker(id, workerId), (e) => e.CopyTo(ms)));

            return JsonConvert.DeserializeObject<ComputationResult[]>(Encoding.UTF8.GetString(ms.ToArray()));
        }

        public void DeleteComputationResults(string id, int workerId)
        {
            Task.WaitAll(_client.RemoveObjectAsync(_bucketName, GetResultKeyForWorker(id, workerId)));
        }

        private static string GetResultKey(string id)
        {
            return $"{id}_result";
        }

        private static string GetTaskKeyForWorker(string id, int workerId)
        {
            return $"{id}_tasks_worker_{workerId}";
        }

        private static string GetResultKeyForWorker(string id, int workerId)
        {
            return $"{id}_results_worker_{workerId}";
        }
    }
}