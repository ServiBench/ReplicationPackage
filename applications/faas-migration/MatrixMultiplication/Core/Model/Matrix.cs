using System.Collections.Generic;
using System.Reflection.Metadata.Ecma335;
using System.Runtime.Serialization;
using System.Text;

namespace MatrixMul.Core.Model
{
    [DataContract]
    public class Matrix
    {
        [DataMember] public int Size { get; set; }
        [DataMember] public List<List<long>> Data { get; set; }

        public long GetAverage()
        {
            long count = 0;
            long avg = 0;

            foreach (var ints in Data)
            {
                foreach (var val in ints)
                {
                    count++;
                    avg += val;
                }
            }

            return avg / count;
        }

        public long GetMin()
        {
            long min = long.MaxValue;

            foreach (var ints in Data)
            {
                foreach (var val in ints)
                {
                    if (val < min)
                    {
                        min = val;
                    }
                }
            }

            return min;
        }

        public long GetMax()
        {
            long max = long.MinValue;

            foreach (var ints in Data)
            {
                foreach (var val in ints)
                {
                    if (val > max)
                    {
                        max = val;
                    }
                }
            }

            return max;
        }

        public MatrixInfo ToMatrixInfo()
        {
            return new MatrixInfo
            {
                Average = GetAverage(),
                Maximum = GetMax(),
                Minimum = GetMin()
            };
        }

        public string ToString()
        {
            var builder = new StringBuilder();

            builder.Append($"{Size}x{Size} Matrix\n");

            for (var i = 0; i < Data.Count; i++)
            {
                var line = Data[i];
                for (var j = 0; j < line.Count; j++) builder.Append($"{line[j]:D10} ");

                builder.Append("\n");
            }

            return builder.ToString();
        }
    }
}