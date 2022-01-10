using System.IO;
using System.Text;
using Xunit.Abstractions;

namespace MatrixMul.Tests
{
    public class XUnitTestWriter : TextWriter
    {
        private ITestOutputHelper _out;

        public XUnitTestWriter(ITestOutputHelper @out)
        {
            _out = @out;
        }

        public override Encoding Encoding => Encoding.Default;

        public override void WriteLine(string value)
        {
            _out.WriteLine(value);
        }
    }
}