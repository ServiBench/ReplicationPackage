using System;
using MatrixMul.Core;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace MatrixMul.IBMCloud
{
    public class GenerateReport
    {
        public JObject Main(JObject args)
        {
            try
            {
                var repo = new CloudObjectStorageRepository(args);
                var hndlr = new FunctionHandler(repo);

                Console.WriteLine("Generating Report");
                
                var callback = "";
                if (args.ContainsKey("hasCallback") && args["hasCallback"].ToString() == "true")
                {
                    Console.WriteLine("Using Callback");
                    callback = args["callback"].ToString();
                }
                else
                {
                    callback = null;
                }

                Console.WriteLine("Reading Start Timestamp");
                var start = long.Parse(args["startTimestamp"].ToString());

                var report = hndlr.GenerateReport(callback, start, args["id"].ToString(),
                    int.Parse(args["worker_count"].ToString()));

                var l = JsonConvert.SerializeObject(report);

                Console.WriteLine(l);
                return JObject.Parse(l);
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