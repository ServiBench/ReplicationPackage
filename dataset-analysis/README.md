# Experiment Data Analysis

## Quick Setup

1. Install Python 3.7+
2. Install the Python dependencies (preferably in a virtual environment)

    ```sh
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

3. Adjust the data source path in `sb_importer.py` (data_path and lg_name)
4. Run analysis

    a) Plain Python

      ```sh
      python coldstart_behavior.py
      python workload_types.py
      python load_levels.py
      python execution.py
      ```

    b) VSCode Interactive: Run individual cells with the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) in [interactive mode](https://youtu.be/lwN4-W1WR84?t=107)

## Experiments

## Prestudy April 2021

* lg2: us-east-1f, t3.xlarge (400gb, gp3)
  * 61.84G (72G disk)
  * contains 26 unlabeled executions not directly assigned to an experiment (mostly used for testing and kept for reference)
* lg3: eu-west-1, t3.xlarge (300gb, gp3)
  * 8.92G (23G disk)
  * video processing only one execution for steady workload
* lg4: us-west-2, t3.xlarge (300gb, gp3)
  * 40.97G (53G disk)
  * event processing logs missing
* lg5: eu-central-1, t3.xlarge (300gb, gp3) => stuff failed for some reasons, aborted!
* lg6: us-east-2c, t3.xlarge (300gb, gp3)
  * 6.76G (13G disk)

### Done

* exp21: 2021-04-28 +1 with fully constant 20rps over 20min, 3 trials
* exp41: 2021-04-29 ramping VUs 1, 10, 20, 50, 100, 1 trial
* exp42: 2021-04-30 +1 fine-grained stepwise from 1 to 200 [1, 10, 20, 50, 100, 150, 200], 1 trial
* exp43: 2021-04-30 ramping rps with thumbnail (40img) only [1, 10, 20, 50, 100, 150, 200, 500, 750, 1000]
* exp22: 2021-04-29 +1 fine-grained stepwise from 1 to 200 [1, 10, 20, 50, 100, 150, 200], 3 trials
  * hello retails appears missing
* exp44: 2021-04-30 ramping rps with event processing (or thumbnail?!) only [1, 10, 20, 50, 100, 150, 200, 500, 750, 1000]
  * no data available
* exp61: 2021-04-30 1h scenarios with event processing app and same avg request rate (72rps, avg = ~4363 from bursty_1h): constant_1h.csv, bursty_1h.csv
* exp31: 2021-04-29 +1 high rps patterns (20rps), 4 patterns * 9 apps, 1 trial each
  * There appears to be some systematic issue where traces of the first 5' are not available? => or debug analysis script!
  * Video processing app seems to have only 1 execution for constant trace workload
* lg3_clean: anonymized traces of exp31 by replacing account id with 123456789012

* lg7: 2021-08-27 load level tests with thumbnail_generator
* lg10: 2021-11-18 ran exp81_xray_sampling with increasing load to explore possible xray sampling configurations
* lg11: 2021-12-07 - 2021-12-10 ran exp1_latency_breakdown v1-v4 to find a suitable strategy for generating cold invocation samples under the given xray limitations
* lg12: data for exp1_latency_breakdown results in paper using bursts of 20 VUs, round robin invocations, and period re-deployment

### Running/Scheduled

### Preparing


## Troubleshooting
