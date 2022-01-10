using System.Collections.Generic;
using MatrixMul.Core.Interfaces;
using MatrixMul.Core.Model;

namespace MatrixMul.Tests
{
    public class MockRepository : IMatrixMulRepository
    {
        private readonly Dictionary<string, MatrixCalculation> _calculations = new Dictionary<string, MatrixCalculation>();
        private readonly Dictionary<string, Matrix> _results = new Dictionary<string, Matrix>();

        private readonly Dictionary<string, Dictionary<int, ComputationTask[]>> _tasks =
            new Dictionary<string, Dictionary<int, ComputationTask[]>>();

        private readonly Dictionary<string, Dictionary<int, ComputationResult[]>> _workerResults =
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
            if (!_tasks.ContainsKey(id))
            {
                _tasks.Add(id, new Dictionary<int, ComputationTask[]>());
            }

            _tasks[id].Add(workerId, tasks);
        }

        public ComputationTask[] GetComputationTasksForWorker(string id, int workerId)
        {
            return _tasks[id][workerId];
        }

        public void DeleteComputationTasks(string id, int workerId)
        {
            // Nothing to Do here
        }

        public void StoreComputationResults(string id, int worker, ComputationResult[] results)
        {
            if (!_workerResults.ContainsKey(id))
            {
                _workerResults.Add(id, new Dictionary<int, ComputationResult[]>());
            }

            _workerResults[id].Add(worker, results);
        }

        public ComputationResult[] GetComputationResults(string id, int worker)
        {
            return _workerResults[id][worker];
        }

        public void DeleteComputationResults(string id, int workerid)
        {
            // Nothing to Do here
        }
    }
}