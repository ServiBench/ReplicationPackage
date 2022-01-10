using System.Collections.Generic;
using MatrixMul.Core.Interfaces;
using MatrixMul.Core.Model;

namespace MatrixMul.Core
{
    public class ComputationHandler
    {
        public Matrix SerialMultiply(MatrixCalculation calculation)
        {
            var n = calculation.A.Size;
            var matrix = Util.GenerateMatrix(n, (x, y) => 0);

            for (var x = 0; x < n; x++)
            for (var y = 0; y < n; y++)
            {
                var res = 0L;
                for (var i = 0; i < n; i++)
                {
                    var a = calculation.A.Data[x][i];
                    var b = calculation.B.Data[i][y];
                    res += a * b;
                }

                matrix.Data[x][y] = res;
            }

            return matrix;
        }

        public Dictionary<int, List<ComputationTask>> BuildTasks(int workerCount, MatrixCalculation calculation)
        {
            var tasks = new Dictionary<int, List<ComputationTask>>();
            var n = calculation.A.Size;

            var cnt = 0;

            for (var x = 0; x < n; x++)
            for (var y = 0; y < n; y++)
            {
                var workerNo = cnt % workerCount;
                if (!tasks.ContainsKey(workerNo)) tasks[workerNo] = new List<ComputationTask>();

                tasks[workerNo].Add(new ComputationTask
                {
                    X = (ushort) x,
                    Y = (ushort) y
                });
                cnt++;
            }

            return tasks;
        }

        public List<ComputationResult> PerformCalculations(int workerID, List<ComputationTask> tasks,
            MatrixCalculation calculation)
        {
            var results = new List<ComputationResult>();
            var n = calculation.A.Size;

            foreach (var computationTask in tasks)
            {
                var res = 0L;
                for (var i = 0; i < n; i++)
                {
                    var a = calculation.A.Data[computationTask.X][i];
                    var b = calculation.B.Data[i][computationTask.Y];
                    res += a * b;
                }

                results.Add(new ComputationResult
                {
                    X = computationTask.X,
                    Y = computationTask.Y,
                    Result = res
                });
            }

            return results;
        }

        public Matrix BuildResultMatrix(MatrixCalculation calculation, List<List<ComputationResult>> results)
        {
            var n = calculation.A.Size;
            var resultMatrix = Util.GenerateMatrix(n, (x, y) => 0);

            foreach (var workerResults in results)
            foreach (var result in workerResults)
                resultMatrix.Data[result.X][result.Y] = result.Result;

            return resultMatrix;
        }
    }
}