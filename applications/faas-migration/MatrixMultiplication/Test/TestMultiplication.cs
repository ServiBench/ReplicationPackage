using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using MatrixMul.Core;
using Microsoft.VisualBasic.CompilerServices;
using Newtonsoft.Json;
using Xunit;
using Xunit.Abstractions;

namespace MatrixMul.Tests
{
    public class TestMultiplication
    {
        public const int Seed = 123321;
        public const int Max = 100;
        public const int Size = 50;

        private ITestOutputHelper _out;
        private MockRepository repo;
        private FunctionHandler hndlr;

        public TestMultiplication(ITestOutputHelper @out)
        {
            _out = @out;

            Console.SetOut(new XUnitTestWriter(@out));

            repo = new MockRepository();
            hndlr = new FunctionHandler(repo);
        }

        [Fact]
        public void TestParallelMulBySeed()
        {
            var start = Util.GetUnixTimestamp();
            _out.WriteLine($"Creating 2 {Size}x{Size} Matrices with Max Value {Max} based on seed {Seed}");
            var id = hndlr.CreateMatrix(Size, Max, Seed);
            _out.WriteLine($"Got ID {id}");

            _out.WriteLine($"Running parallel Multiply");
            hndlr.ScheduleMultiplicationTasks(id, 5);
            var tasks = new List<Task>();
            for (int i = 0; i < 5; i++)
            {
                _out.WriteLine($"Running Worker #{i}");
                hndlr.ParallelMultiplyWorker(id, i);
            }

            _out.WriteLine("Building Result");
            hndlr.BuildResultMatrix(id, 5);

            _out.WriteLine("Creating Report");
            var report = hndlr.GenerateReport(null, start, id, 0);
            _out.WriteLine(report.ToString());

            _out.WriteLine("A:");
            _out.WriteLine(repo.GetCalculation(id).A.ToString());
            _out.WriteLine("B:");
            _out.WriteLine(repo.GetCalculation(id).B.ToString());
            _out.WriteLine("Result:");
            _out.WriteLine(repo.GetResultMatrix(id).ToString());

            Assert.Equal(121672, report.ResultMatrix.Average);
            Assert.Equal(78312, report.ResultMatrix.Minimum);
            Assert.Equal(168397, report.ResultMatrix.Maximum);
        }

        [Fact]
        public void TestParallelMulByZero()
        {
            var start = Util.GetUnixTimestamp();
            _out.WriteLine($"Creating 2 {Size}x{Size} Matrices");
            var id = hndlr.CreateMatrix(Size, Max, Seed, (x, y) => 0);
            _out.WriteLine($"Got ID {id}");

            _out.WriteLine($"Running parallel Multiply");
            hndlr.ScheduleMultiplicationTasks(id, 5);
            var tasks = new List<Task>();
            for (int i = 0; i < 5; i++)
            {
                _out.WriteLine($"Running Worker #{i}");
                hndlr.ParallelMultiplyWorker(id, i);
            }

            _out.WriteLine("Building Result");
            hndlr.BuildResultMatrix(id, 5);


            _out.WriteLine("Creating Report");
            var report = hndlr.GenerateReport(null, start, id, 0);
            _out.WriteLine(report.ToString());

            _out.WriteLine("A:");
            _out.WriteLine(repo.GetCalculation(id).A.ToString());
            _out.WriteLine("B:");
            _out.WriteLine(repo.GetCalculation(id).B.ToString());
            _out.WriteLine("Result:");
            _out.WriteLine(repo.GetResultMatrix(id).ToString());

            foreach (var xs in repo.GetResultMatrix(id).Data)
            {
                foreach (var l in xs)
                {
                    Assert.Equal(0, l);
                }
            }

            Assert.Equal(0, report.ResultMatrix.Average);
            Assert.Equal(0, report.ResultMatrix.Minimum);
            Assert.Equal(0, report.ResultMatrix.Maximum);
        }

        [Fact]
        public void TestParallellMulByIdentity()
        {
            var start = Util.GetUnixTimestamp();
            _out.WriteLine($"Creating 2 {Size}x{Size} Matrices");
            var id = hndlr.CreateMatrix(Size, Max, Seed, (x, y) => x == y ? 1 : 0);
            _out.WriteLine($"Got ID {id}");

            _out.WriteLine($"Running parallel Multiply");
            hndlr.ScheduleMultiplicationTasks(id, 5);
            var tasks = new List<Task>();
            for (int i = 0; i < 5; i++)
            {
                _out.WriteLine($"Running Worker #{i}");
                hndlr.ParallelMultiplyWorker(id, i);
            }

            _out.WriteLine("Building Result");
            hndlr.BuildResultMatrix(id, 5);

            _out.WriteLine("Creating Report");
            var report = hndlr.GenerateReport(null, start, id, 0);
            _out.WriteLine(report.ToString());

            _out.WriteLine("A:");
            _out.WriteLine(repo.GetCalculation(id).A.ToString());
            _out.WriteLine("B:");
            _out.WriteLine(repo.GetCalculation(id).B.ToString());
            _out.WriteLine("Result:");
            _out.WriteLine(repo.GetResultMatrix(id).ToString());

            var result = repo.GetResultMatrix(id);
            var b = repo.GetCalculation(id).B;

            for (var i = 0; i < b.Data.Count; i++)
            {
                for (var j = 0; j < b.Data[i].Count; j++)
                {
                    Assert.Equal(b.Data[i][j], result.Data[i][j]);
                }
            }

            Assert.Equal(49, report.ResultMatrix.Average);
            Assert.Equal(0, report.ResultMatrix.Minimum);
            Assert.Equal(99, report.ResultMatrix.Maximum);
        }

        [Fact]
        public void TestSerialMulBySeed()
        {
            var start = Util.GetUnixTimestamp();
            _out.WriteLine($"Creating 2 {Size}x{Size} Matrices with Max Value {Max} based on seed {Seed}");
            var id = hndlr.CreateMatrix(Size, Max, Seed);
            _out.WriteLine($"Got ID {id}");

            _out.WriteLine($"Running serial Multiply");
            hndlr.SerialMultiply(id);

            _out.WriteLine("Creating Report");
            var report = hndlr.GenerateReport(null, start, id, 0);
            _out.WriteLine(report.ToString());

            _out.WriteLine("A:");
            _out.WriteLine(repo.GetCalculation(id).A.ToString());
            _out.WriteLine("B:");
            _out.WriteLine(repo.GetCalculation(id).B.ToString());
            _out.WriteLine("Result:");
            _out.WriteLine(repo.GetResultMatrix(id).ToString());

            Assert.Equal(121672, report.ResultMatrix.Average);
            Assert.Equal(78312, report.ResultMatrix.Minimum);
            Assert.Equal(168397, report.ResultMatrix.Maximum);
        }

        [Fact]
        public void TestSerialMulByZero()
        {
            var start = Util.GetUnixTimestamp();
            _out.WriteLine($"Creating 2 {Size}x{Size} Matrices");
            var id = hndlr.CreateMatrix(Size, Max, Seed, (x, y) => 0);
            _out.WriteLine($"Got ID {id}");

            _out.WriteLine($"Running serial Multiply");
            hndlr.SerialMultiply(id);

            _out.WriteLine("Creating Report");
            var report = hndlr.GenerateReport(null, start, id, 0);
            _out.WriteLine(report.ToString());

            _out.WriteLine("A:");
            _out.WriteLine(repo.GetCalculation(id).A.ToString());
            _out.WriteLine("B:");
            _out.WriteLine(repo.GetCalculation(id).B.ToString());
            _out.WriteLine("Result:");
            _out.WriteLine(repo.GetResultMatrix(id).ToString());

            foreach (var xs in repo.GetResultMatrix(id).Data)
            {
                foreach (var l in xs)
                {
                    Assert.Equal(0, l);
                }
            }

            Assert.Equal(0, report.ResultMatrix.Average);
            Assert.Equal(0, report.ResultMatrix.Minimum);
            Assert.Equal(0, report.ResultMatrix.Maximum);
        }

        [Fact]
        public void TestSerialMulByIdentity()
        {
            var start = Util.GetUnixTimestamp();
            _out.WriteLine($"Creating 2 {Size}x{Size} Matrices");
            var id = hndlr.CreateMatrix(Size, Max, Seed, (x, y) => x == y ? 1 : 0);
            _out.WriteLine($"Got ID {id}");

            _out.WriteLine($"Running serial Multiply");
            hndlr.SerialMultiply(id);

            _out.WriteLine("Creating Report");
            var report = hndlr.GenerateReport(null, start, id, 0);
            _out.WriteLine(report.ToString());

            _out.WriteLine("A:");
            _out.WriteLine(repo.GetCalculation(id).A.ToString());
            _out.WriteLine("B:");
            _out.WriteLine(repo.GetCalculation(id).B.ToString());
            _out.WriteLine("Result:");
            _out.WriteLine(repo.GetResultMatrix(id).ToString());

            var result = repo.GetResultMatrix(id);
            var b = repo.GetCalculation(id).B;

            for (var i = 0; i < b.Data.Count; i++)
            {
                for (var j = 0; j < b.Data[i].Count; j++)
                {
                    Assert.Equal(b.Data[i][j], result.Data[i][j]);
                }
            }

            Assert.Equal(49, report.ResultMatrix.Average);
            Assert.Equal(0, report.ResultMatrix.Minimum);
            Assert.Equal(99, report.ResultMatrix.Maximum);
        }

        [Fact]
        public void GetParallelTestReport()
        {
            var start = Util.GetUnixTimestamp();
            _out.WriteLine($"Creating 2 {Size}x{Size} Matrices with Max Value {Max} based on seed {Seed}");
            var id = hndlr.CreateMatrix(Size, Max, Seed);
            _out.WriteLine($"Got ID {id}");

            _out.WriteLine($"Running serial Multiply");
            hndlr.SerialMultiply(id);

            _out.WriteLine("Creating Report");
            var report = hndlr.GenerateReport(null, start, id, 0);

            var reportstr = JsonConvert.SerializeObject(report);
            _out.WriteLine(reportstr);
        }
        
        [Fact]
        public void GetSerialTestReport()
        {
            var start = Util.GetUnixTimestamp();
            _out.WriteLine($"Creating 2 {Size}x{Size} Matrices with Max Value {Max} based on seed {Seed}");
            var id = hndlr.CreateMatrix(9, Max, Seed);
            _out.WriteLine($"Got ID {id}");

            _out.WriteLine($"Running serial Multiply");
            hndlr.SerialMultiply(id);

            _out.WriteLine("Creating Report");
            var report = hndlr.GenerateReport(null, start, id, 0);

            var reportstr = JsonConvert.SerializeObject(report);
            _out.WriteLine(reportstr);
        }
    }
}