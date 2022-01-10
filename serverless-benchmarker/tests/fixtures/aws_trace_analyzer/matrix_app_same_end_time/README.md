# Assertion Error



## SB Error

```
Segment with latest end time (1b666be485f96295) does not match last target (cc765bcfefc2f724) of critical path.
```

Interestingly, these two segments have exactly the same end_time of `1639806386.906` according to the web and API-retrieved trace.

* cc765bcfefc2f724: 1.639806386906E9
* 1b666be485f96295: 1.639806386906E9

This might be a validation bug in the trace analyzer:

* If the lastest end time is the same for multiple segments, the identification of the right end segment might fail.
* The critical path analyzer (which is the relevant part for the results) appears correct in this case because it is based on more detailed causual information in addition to timestamps.
* Hence, this might be a false positive validation error but the identification of G.graph['end'] (i.e., the last end node based on time) seems incorrect when multiple identical timestamps exist.

The same issue also appears in several other apps. For example:
* lg12/aws-serverless-workshops/ImageProcessing/logs/2021-12-15_11-25-15: `1-61b9d09d-a6764bc06b3ab9ae052b8825	Segment with latest end time (1838a0fe44d44fdf) does not match last target (faa9e368fd7f9f42) of critical path.`
