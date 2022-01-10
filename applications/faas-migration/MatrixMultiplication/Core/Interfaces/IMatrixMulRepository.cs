using System.Runtime.InteropServices;
using MatrixMul.Core.Model;

namespace MatrixMul.Core.Interfaces
{
    /// <summary>
    ///     This interface represents a "datastore" used to buffer the data of the computation
    ///     The ids given to the methods are guaranteed to identify this calculation exactly
    /// </summary>
    public interface IMatrixMulRepository
    {
        /// <summary>
        ///     Store a Calculation, this includes serializing it
        ///     This Method can throw any exception in case something goes wrong!
        /// </summary>
        /// <param name="id">The id to store the object at. The Function handler used Guid.New().ToString() to create this value</param>
        /// <param name="calculation">the calculation to store</param>
        void StoreCalculation(string id, MatrixCalculation calculation);

        /// <summary>
        ///     Retrieve and deserialize a calculation
        ///     This Method can throw any exception in case something goes wrong!
        /// </summary>
        /// <param name="id">The id to retrieve</param>
        /// <returns>The deserialized Calculation object</returns>
        MatrixCalculation GetCalculation(string id);

        /// <summary>
        ///     Delete the matrix calculation with the given ID
        ///     This Method can throw any exception in case something goes wrong!
        /// </summary>
        /// <param name="id">The id to Delete</param>
        void DeleteCalculation(string id);

        /// <summary>
        ///     Store a result matrix
        /// </summary>
        /// <param name="id">the id of the calculation to which this matrix belongs</param>
        /// <param name="matrix">The Matrix to store</param>
        void StoreResultMatrix(string id, Matrix matrix);
        Matrix GetResultMatrix(string id);
        void DeleteResultMatrix(string id);

        /// <summary>
        ///     Store computation tasks for a worker function
        ///     This Method can throw any exception in case something goes wrong!
        /// </summary>
        /// <param name="id">the id of the calculation to which this matrix belongs</param>
        /// <param name="tasks">The Array of tasks to store</param>
        /// <param name="workerId">The id number of the worker</param>
        void StoreComputationTasksForWorker(string id, int workerId, ComputationTask[] tasks);
        /// <summary>
        ///     Get computation results of a worker function
        ///     This Method can throw any exception in case something goes wrong!
        /// </summary>
        /// <param name="id">the id of the calculation to which this matrix belongs</param>
        /// <param name="workerId">The id number of the worker</param>
        /// <returns>the array of results produced by the worker</returns>
        ComputationTask[] GetComputationTasksForWorker(string id, int workerId);
        /// <summary>
        ///     Delete computation tasks of a worker function
        ///     This Method can throw any exception in case something goes wrong!
        /// </summary>
        /// <param name="id">the id of the calculation to which the tasks belong</param>
        /// <param name="workerId">The id number of the worker</param>
        void DeleteComputationTasks(string id, int workerId);

        /// <summary>
        ///     Store computation results from a worker function
        ///     This Method can throw any exception in case something goes wrong!
        /// </summary>
        /// <param name="id">the id of the calculation to which the results belong</param>
        /// <param name="results">The Array of tasks to store</param>
        /// <param name="worker">The id number of the worker</param>
        void StoreComputationResults(string id, int worker, ComputationResult[] results);
        /// <summary>
        ///     Get computation results of a worker function
        ///     This Method can throw any exception in case something goes wrong!
        /// </summary>
        /// <param name="id">the id of the calculation to which the results belong</param>
        /// <param name="worker">The id number of the worker</param>
        /// <returns>the array of results produced by the worker</returns>
        ComputationResult[] GetComputationResults(string id, int worker);
        /// <summary>
        ///     Delete computation results of a worker function
        ///     This Method can throw any exception in case something goes wrong!
        /// </summary>
        /// <param name="id">the id of the calculation to which the results belong</param>
        /// <param name="worker">The id number of the worker</param>
        /// <returns>the array of results produced by the worker</returns>
        void DeleteComputationResults(string id, int workerid);
    }
}