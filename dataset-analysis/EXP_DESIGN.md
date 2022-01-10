# Experiment Design

* region: us-east-1
  * Used by other studies (e.g., copik:21a, wang:18)
  * We could easily look into other regions but we already have many other variables and region doesn't appear the most interesting one to control.
  * Limitation: AWS X-Ray processes data per region, hence cross-region applications would require [custom client-side correlation](https://aws.amazon.com/xray/faqs/#Regions).
* load generator instance type: t3a.large (~12$ weekly)
  * Previously used a t3.xlarge (~25$ weekly) but that was heavily over-provisioned after monitoring CPU utilization for a while.
  * t3a.* instances use AMD processors and are slightly cheaper than t3.* instances
* Sampling decision is taken at the front end service (e.g., API Gateway). Even client-side sampling decision possible.
* Onelogin SSO authentication limitation: Need to refresh credentials at least every 8 hours
* Function size: 1024 MB

## exp1_latency_breakdown (7 days)

used for latency breakdown of warm invocations, delta to cold invocations, delta to slow requests.

Mainly designed around the question: How can we trigger cold starts?
because it's easy to collect warm invocations but takes times to experience cold starts.

* a) Wait x minutes until function is hopefully recycled: (-) about 20ish minutes waiting time => 12.5 days for 100 samples
* b) Redeploy apps after each sample: (-) it takes 5-40 min to deploy certain apps => maybe ~10ish days for 100 samples
* c) use x concurrent requests: (-) high concurrency can affect latency (+) can collect many samples at the same time
* d) use concurrent app deployments: (-) only works across regions or would require time-consuming per-app parametrization
* e) add some generic "function cooler": a 'placebo' function updater that causes cold starts: (-) need to implement some bogus env variable change or memory update (see [StackOverflow](https://stackoverflow.com/questions/55206348/how-do-i-force-a-complete-cold-start-of-an-aws-lambda-function-on-a-vpc))

=> Collect cold and warm measurements together for comparable data source because some warm invocations basically come for free after a cold start
Going for c) concurrent request appears the easiest but likely introduces variability due to scaling (i.e., measuring something else). Using 30 VU (NOT rps!) for 60s collects roughly 30ish (maybe a few less 'full' cold starts) cold start samples per deployment (or per 20ish minutes).
Caveat: We are testing under concurrency of 30VU, hence some contention might be part of this baseline then.

Sequential with re-deployment:

* prepare1 (6')
* invoke1 (1')
* wait (5') => depends on load rate, could skip when using an interlaced schedule (challenge: avoid overlapping!)
* get_traces (1')
* cleanup (3')
~20min for a full cycle of 30ish cold invocation samples per app * 9 apps
=> 3h for 30 samples

make chunks of 9h for 90 samples
takes roughly a week for 1000ish samples when run twice a day. Might be able to increase with continuous credentials refreshing.

=> with 60s runtime at 30 VU, that's more than 1500x more warm invocations than cold invocations (e.g., 3000 vs 5 million)

NOTE: ustiugov:21a (STeLLAR) collects 3000 samples per configuration but they can use many identical (simple) functions. This is not possible with our more complex apps because it would require randomizing all names.

* multi-region: We could use multiple regions simultaneously to speed up sample collection and validate results across regions. Challenge: different regions might yield slightly different absolute results.
* avoid re-deploy: Instead of re-deploying, we could just schedule invocation trials in sequence, which should (hopefully) be enough time to recycle the instance.

NOTE: should report median deployment times on the standardized EC2 machine.

* repetitions: Should we have multiple repetitions in addition to iterations?
  * If so, how do we aggregate across repetitions?
* time: Should we schedule repetitions at different days / time of the day?
* cost:
  * Secondary: If possible scheduling some experiments in different hours could help to properly attribute cost per app.
  * Download cost explorer logs after execution

### Application Parameters

* thumbnail_generator:
  * num_different_images=20 (max 40ish due to memory limitations)
* model_training:
  * data_replication=20
* video_processing:
  * data_replication=20

## exp2_load_levels (3 days)

REMINDER: Save trace_timeline.pdf when looking up error traces in X-Ray.

* 1 rps
* 10 rps
* 20 rps
* 30 rps
  * matrix_multiplication reached 13% invalid traces
  * NOTE: executed as a later iteration because we skipped it initially going for doubling load levels but then noticed we need more fine grained steps here.
* 40 rps
  * matrix_multiplication kept 85% invalid traces due to pending traces running into the X-Ray limitation. `faas-migration/MatrixMultiplication/Lambda/logs/2021-12-30_16-48-28`
    * Reduce sampling invocation rate of X-Ray such that traces are not invalid using a fixed rate.
* 50 rps
* 60 rps
  * image_processing reached 58% error rate (+8% over probabilistic 50% baseline)
* 70 rps
  * image_processing kept 64% error rate (+14% over probabilistic 50% baseline) => remove
    * NOTE: image_processing app is limited to 50rps by Rekognition service in us-east-1 (2021-04-27) but only 5rps in most other regions! See [comment](https://github.com/anonymous/aws-serverless-workshops/blob/master/ImageProcessing/src/lambda-functions/face-detection/index.js#L24).
  * thumbnail_generator reached 5% error rate running into S3 throttle
* 80 rps
  * thumbnail_generator reset 4% error rate
* 90 rps
  * thumbnail_generator reached 7% error rate
* 100 rps
  * thumbnail_generator kept 7% error rate => remove (missed)
  * event_processing reached 5% invalid traces
* 120 rps
  * event_processing reached 25% invalid traces due to in progress
  * thumbnail_generator kept (2nd time) 11% error rate => remove
* 140 rps
  * event_processing kept 47% invalid traces due to in progress => remove
  * video_processing reached 6% error rate due to S3 throttling (rate limit)
* 160 rps
  * video_processing kept 7% error rate => remove
* 180 rps
* 200 rps
* 250 rps
* 300 rps
* 400 rps
  * NOTE: seemingly executed twice (iteration 18+19)
  * model_training has many dropped iterations (only achieving 42 r/sec) => remove
* 500 rps
  * todo_api reached 24% invalid traces due to missing and pending (in progress) AWS::Lambda segments
  * hello_retail reached 12% invalid traces
  * apigw_node reached 12% invalid traces
* 600 rps
  * todo_api kept 32% invalid traces
  * hello_retail kept 24% invalid traces
  * apigw_node kept 14% invalid traces
  * realworld_backend reached 16% invalid traces
* 700 rps
  * realworld_backend kept 31% invalid traces


Upcoming errors:
  * hello_retail: stepfunctions timeout (somehow always staying around 3%)

Validation:
* Check how closely the load levels could be reached => monitor lg on high load and check logs!
  * model_training + video_processing never seems to catch up with the load due to it's long execution
  * hello_retail remains slightly under the specified load level
  * other apps are good

Question: What load level issues should we address before moving on to workload types?

* discrepancy between actual vs target load => higher spec load generator
* invalid traces => reduce sampling rate
* error rates => configure storage replica for thumbnail_generator + video_processing app fixes hot bucket key access

5 levels * 10 apps * 30min => ~22h

Runtime: 90s
Threshold: 95% success (i.e., less than 5% error rate)
NOTE: threshold applied on a per-application basis (not per request type)

Process:
* Run load level for all apps and only proceed to next load levels with apps that fulfill the success threshold. Re-deploy before proceeding to next load level.
=> identify threshold for each app (could use binary search with -50rps to find threshold more fine-grained)

app params: We might need to increase app parameters for higher load levels.
AWS limits: Do we report results based on standard limits or should we raise the limits?
=> document in paper per service per app as showcase how to use tracing: document when which limit hit, then increase rate

## exp3_workload_types (2 days)

### artificial

* constant: fully constant load
* on_off: same average load as constant but with extreme bursts. For example, 3s 0rps, then 1s burst

Trial runs:

```none
exp3_workload_types_on_off_10
exp3_workload_types_on_off_10
exp3_workload_types_on_off_10_constant_arrival_rate

serverless-patterns/apigw-lambda-cdk/src/logs/2022-01-04_21-42-19
serverless-patterns/apigw-lambda-cdk/src/logs/2022-01-04_22-07-20
serverless-patterns/apigw-lambda-cdk/src/logs/2022-01-04_22-33-57
```

### realistic

* steady
* fluctuating (formerly bursty but that's too overloaded)
* jump
* spikes

=> total number of requests should to be the same for all workload types
=> pick 'representative' workload sample
=> use linear scaling to adjust for same total number of request and per app based on results of exp2

20 min input generates 17 min actual runtime

=> Maybe choose intensity based on output of load level experiment?

Challenge: How to choose the load level for the workload types?
a) Use implemented scaling (linear or compound) to adjust load level depending on app based on the results from exp2_load_levels (e.g., something around or right below the last success load level)
b) Pick different traces (-) cannot make argument for 'fair' comparison between different traces anymore.

Proposed solution: Pick 'representative' workload type and use scaling to adjust per app. The goal is to run each app such that the max rps in a trace maps roughly to the maximal load level.

## Prepare Durations

Rough estimates based on lg3 (t3a.xlarge, us-east-1).

* image_processing: 2:35 | 155
* todo_api: 2:00 | 120
* event_processing: 14:00 | 840
* matrix_multiplication: 2:00 | 120
* thumbnail_generator: 2:15 | 135
* hello_retail: 20:00 | 1200
* realworld_backend: 2:30 | 150
* model_training: 4:00 | 240
* video_processing: 5:00 | 300

=> avg prepare time: 6:00 | 360s

## Overall Notes

* The evaluation is more of a characterization rather than an apple-to-apple comparison because different applications are inherently different.
* We don't propose any performance improvements that we could evaluate against a suitable baseline.
* Possible threat: Why are you using request rates and not concurrency levels (i.e., VU) given that the number of parallel functions is key?
* We cannot evaluate how realistic our trace-generation approach is. Maybe test against smaller Alibaba Cloud Functions dataset from FaaSNet (wang:21a)?
* We do not evaluate how accurate our classification is. We describe the methodology/algorithm and have manually verified test cases but there is not really a ground truth. A colorized version of the trace visualizer could help to make this argument with example visualizations.
