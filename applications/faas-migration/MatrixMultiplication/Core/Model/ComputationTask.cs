using System.Runtime.Serialization;

namespace MatrixMul.Core.Model
{
    [DataContract]
    public class ComputationTask
    {
        [DataMember] public ushort X { get; set; }
        [DataMember] public ushort Y { get; set; }
    }
}