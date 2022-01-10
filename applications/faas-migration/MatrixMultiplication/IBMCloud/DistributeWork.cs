using System;
using MatrixMul.Core;
using Newtonsoft.Json.Linq;

namespace MatrixMul.IBMCloud
{
    public class DistributeWork
    {
        public JObject Main(JObject args)
        {
            try
            {
                var repo = new CloudObjectStorageRepository(args);
                var hndlr = new FunctionHandler(repo);

                hndlr.ScheduleMultiplicationTasks(args["id"].ToString(), int.Parse(args["worker_count"].ToString()));

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