using System.Runtime.Serialization;

namespace MatrixMul.Core.Model
{
    [DataContract]
    public class Report
    {
        [DataMember(IsRequired = true)] public int Size { get; set; }
        [DataMember(IsRequired = true)] public MatrixInfo InputMatrixA { get; set; }
        [DataMember(IsRequired = true)] public MatrixInfo InputMatrixB { get; set; }
        [DataMember(IsRequired = true)] public MatrixInfo ResultMatrix { get; set; }
        [DataMember(IsRequired = true)] public long StartTimestamp { get; set; }
        [DataMember(IsRequired = true)] public long EndTimestamp { get; set; }

        public override string ToString()
        {
            return $"Report(Size = {Size}, InputMatrixA = {InputMatrixA}," +
                   $" InputMatrixB = {InputMatrixB}, ResultMatrix = {ResultMatrix}," +
                   $" StartTimestamp = {StartTimestamp}, EndTimestamp = {EndTimestamp})";
        }
    }

    [DataContract]
    public class MatrixInfo
    {
        [DataMember(IsRequired = true)] public long Average { get; set; }
        [DataMember(IsRequired = true)] public long Minimum { get; set; }
        [DataMember(IsRequired = true)] public long Maximum { get; set; }

        public override string ToString()
        {
            return $"MatrixInfo(Average = {Average}, Minimum = {Minimum}, Maximum = {Maximum})";
        }
    }
}