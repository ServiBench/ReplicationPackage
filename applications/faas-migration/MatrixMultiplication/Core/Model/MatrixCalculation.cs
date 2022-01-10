using System.Runtime.Serialization;

namespace MatrixMul.Core.Model
{
    [DataContract]
    public class MatrixCalculation
    {
        [DataMember] public Matrix A { get; set; }
        [DataMember] public Matrix B { get; set; }
    }
}