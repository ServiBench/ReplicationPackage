using System.Collections.Generic;
using MatrixMul.Core.Interfaces;
using MatrixMul.Core.Model;

namespace MatrixMul.Azure
{
    public class InMemoryMatrixMulRepository : IMatrixMulRepository
    {
        private Dictionary<string, MatrixCalculation> _calculations = new Dictionary<string, MatrixCalculation>();
        private Dictionary<string, Matrix> _results = new Dictionary<string, Matrix>();

        public Dictionary<string, Dictionary<int, ComputationTask[]>> Tasks =
            new Dictionary<string, Dictionary<int, ComputationTask[]>>();

        public Dictionary<string, Dictionary<int, ComputationResult[]>> WorkerResults =
            new Dictionary<string, Dictionary<int, ComputationResult[]>>();

        public void StoreCalculation(string id, MatrixCalculation calculation)
        {
            _calculations.Add(id, calculation);
        }

        public MatrixCalculation GetCalculation(string id)
        {
            return _calculations[id];
        }

        public void DeleteCalculation(string id)
        {
            _calculations.Remove(id);
        }

        public void StoreResultMatrix(string id, Matrix matrix)
        {
            _results.Add(id, matrix);
        }

        public Matrix GetResultMatrix(string id)
        {
            return _results[id];
        }

        public void DeleteResultMatrix(string id)
        {
            // Nothing to Do here
        }

        public void StoreComputationTasksForWorker(string id, int workerId, ComputationTask[] tasks)
        {
            if (!Tasks.ContainsKey(id))
            {
                Tasks.Add(id, new Dictionary<int, ComputationTask[]>());
            }

            Tasks[id].Add(workerId, tasks);
        }

        public ComputationTask[] GetComputationTasksForWorker(string id, int workerId)
        {
            return Tasks[id][workerId];
        }

        public void DeleteComputationTasks(string id, int workerId)
        {
            // Nothing to Do here
        }

        public void StoreComputationResults(string id, int worker, ComputationResult[] results)
        {
            if (!WorkerResults.ContainsKey(id))
            {
                WorkerResults.Add(id, new Dictionary<int, ComputationResult[]>());
            }

            WorkerResults[id].Add(worker, results);
        }

        public ComputationResult[] GetComputationResults(string id, int worker)
        {
            return WorkerResults[id][worker];
        }

        public void DeleteComputationResults(string id, int workerid)
        {
            // Nothing to Do here
        }
    }
}