using System;
using System.Collections.Generic;
using MatrixMul.Core.Model;

namespace MatrixMul.Core
{
    public class Util
    {
        public static long GetUnixTimestamp()
        {
            return (long) DateTime.UtcNow.Subtract(new DateTime(1970, 1, 1)).TotalMilliseconds;
        }

        public static string GenerateUUID()
        {
            return Guid.NewGuid().ToString();
        }

        public static Matrix GenerateMatrix(int n, Func<int, int, long> genFunc)
        {
            Console.WriteLine("Creating Matrix");
            var datamatrix = new List<List<long>>();
            for (var x = 0; x < n; x++)
            {
                var l = new List<long>();
                for (var y = 0; y < n; y++) l.Add(genFunc(x, y));

                datamatrix.Add(l);
            }

            return new Matrix
            {
                Data = datamatrix,
                Size = n
            };
        }
    }
}
