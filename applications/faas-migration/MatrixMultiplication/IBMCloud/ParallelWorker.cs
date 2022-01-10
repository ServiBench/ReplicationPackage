using System;
using MatrixMul.Core;
using Newtonsoft.Json.Linq;

namespace MatrixMul.IBMCloud
{
    public class ParallelWorker
    {
        public JObject Main(JObject args)
        {
            try
            {
                var repo = new CloudObjectStorageRepository(args);
                var hndlr = new FunctionHandler(repo);

                hndlr.ParallelMultiplyWorker(args["id"].ToString(), int.Parse(args["worker_id"].ToString()));

                Console.WriteLine(args.ToString());
                return args;
            }
            catch (Exception e)
            {
                var j = new JObject();
                j["error"] = e.ToString();
                return j;
            }
            
            
        }
    }
}