# Trace Debugging

## Things to investigate

1. Latency breakdown validation mismatch could hint towards potential bug in analyzer?! Search for all 93366 occurrences `ag -G '\invalid\_traces.csv$' 'does not match latency breakdown' .` They mostly appear in the event processing app => due to bug in `longest_path` algorithm!
2. Latency breakdown plot exp22:
  * Event processing has several negative computation times (~ -100ms) in all executions
  * Hello retail has unclassified time
  * Image processing has substantial unclassified time

## exp31.py (v2)

Improvements over v1: Recovered 55836 traces by extracting test cases and fixing issues such as different clock accuracies (using time comparison margin).

`faas-migration/ThumbnailGenerator/Lambda/logs/2021-04-30_00-40-03`

* mostly (7851) due to segments in progress.
* Some (54) have "Missing trace duration"
* Few (5) incomplete traces due to missing parent

`faas-migration/ThumbnailGenerator/Lambda/logs/2021-04-30_00-10-50`

* mostly (4440) due to segments "in progress."
* Some (7) due to "Logical first trace segment" do not match the earliest time

`faas-migration/MatrixMultiplication/Lambda/logs/2021-04-30_02-37-53`

* mostly (7277) due to segments "in progress."
* one case of mismatching latency breakdown: `1-608b7225-f9515a90f14df0fa47820bc0,Trace duration 0:00:00.417000 does not match latency breakdown 0:00:00.386000 within margin 0:00:00.001001.`

`faas-migration/MatrixMultiplication/Lambda/logs/2021-04-30_03-07-15`

* mostly (8447) due to segments "in progress."
* Few (21) cases on "Incomplete trace " due to missing parent

`faas-migration/Event-Processing/Lambda/logs/2021-04-30_04-41-31`

* Basically all (18337) do not match latency breakdown

`faas-migration/Event-Processing/Lambda/logs/2021-04-30_05-34-22`

* Basically all (23842) do not match latency breakdown

`faas-migration-go/aws/logs/2021-04-30_10-34-58`

* Mostly (3518) "in progress."
* Some (12) "Incomplete trace " due to missing parent
* Some (43) due to "Logical first trace segment" not matching earliest time

`faas-migration-go/aws/logs/2021-04-30_10-05-38`

* Mostly (3506) "in progress."
* Some (52) due to "Logical first trace segment" not matching earliest time

`serverless-faas-workbench/aws/cpu-memory/video_processing/logs/2021-04-30_16-55-30`

* Mostly (10830) subsegment or segment "in progress." (both but more subsegments)
* Some (11) "Incomplete trace " due to missing parent

`hello-retail/logs/2021-04-30_14-15-59`

* error rate of 4.82 percent (1064 errors in total)
* Almost all errors (1063) have the message message: `Task Timed Out: 'arn:aws:states:eu-west-1:123456789012:activity:dev-hello-retail-product-photos-receive'`

`aws-serverless-workshops/ImageProcessing/logs/2021-04-30_07-02-35`

* error rate of 49.86 appears mainly (mentioned in 15419 traces while 15373 have errors) caused by an intentional error path due to "PhotoDoesNotMeetRequirementError" (e.g., 1-608bac5f-feef4e053d4b9fa008fcb044)

## exp31.py (v1)

`aws-serverless-workshops/ImageProcessing/logs/2021-04-30_07-02-35`

* mostly `1-608bafbd-18a47f36d0429045a6a1c986,Logical first trace segment 63fbb91def18579b does not match the earliest time (sub)segment 0139f6ee699fe665. Ensure that the trace is fully connected and there are no clock issues.`
* also missing, incomplete, and no-message errors

`faas-migration-go/aws/logs/2021-04-30_09-06-52`

* mostly no-message errors (almost 60% !!!)

`faas-migration/Event-Processing/Lambda/logs/2021-04-30_03-48-52`

* mostly no-message errors ~50% invalid + ~90% missing

`faas-migration/MatrixMultiplication/Lambda/logs/2021-04-30_01-39-03`

* very few invalid
* either in progress or parent node missing

`faas-migration/MatrixMultiplication/Lambda/logs/2021-04-30_03-07-15`

* ~40% but almost all in progress

`hello-retail/logs/2021-04-30_11-21-29`

* few invalid
* either no-message (most), or `Logical first trace segment 01c3a69a4179b295 does not match the earliest time (sub)segment 0317b67c4dd49832. Ensure that the trace is fully connected and there are no clock issues.`
* error of `1-608be97d-b2239b4fe79b3a45b6771f37` due to cause `Task Timed Out: 'arn:aws:states:eu-west-1:123456789012:activity:dev-hello-retail-product-photos-receive` (JS stacktrace attached)

`realworld-dynamodb-lambda/logs/2021-04-30_14-52-50`

* ~3% invalid
* mostly no-message
* few with `1-608c1bd4-8ceba73b6799988cd7aaee1a,Trace duration 0:00:00.035000 does not match the calculated trace duration 0:00:00.035189 based on start and end times. Ensure that the trace is fully connected and there are no clock issues.`
  * ==> Hypothesis: X-Ray traces are not accurate to the latest digit. It appears they round to millisecond accuracy. See: `0:00:00.035000` vs `0:00:00.035189` ANSWER: traces use different time resolutions => fixed through time margin workaround
* also few incomplete because of missing parent or time issue of logical root

`serverless-faas-workbench/aws/cpu-memory/model_training/logs/2021-04-30_17-37-41`

* very few (16) with no-message error

`serverless-faas-workbench/aws/cpu-memory/video_processing/logs/2021-04-30_16-55-30`

* most segment or subsegment in progress
