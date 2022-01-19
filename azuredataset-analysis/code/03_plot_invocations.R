library(tidyverse)

# This script filters relevant traces and generates line plots with
# invocation rates over time for two different time periods.

# Configure Output Directory -----------------------
baseDir <- "../results/invocations/20min_min1rps"
dir.create(baseDir, recursive = TRUE, showWarnings = FALSE)

# Filter Traces for Relevant Classes ---------------------------
filtered <- all %>%
  # Skip timer triggers because they follow very predictable periodic patterns
  # and are typically not latency-critical.
  # Further not many timer triggered functions have high invocation rates:
  # only 26 for very_high (>1/s) and 1769 for high (>1/min)
  filter(Trigger != "timer") %>%
  # Using the total number of invocations from day 1 for the following
  # invocation frequency classes:
  # extreme (>10/s)
  # filter(Count.1 >= 1440*60*10)
  # very_high (>1/s)
  filter(Count.1 >= 1440*60)
  # high (>1/min) corresponds to the red class in [1, Figure 5]
  # filter(Count.1 >= 1440)
  # high_max100k
  # filter(Count.1 >= 1440 & Count.1 <= 100000)
  # high_max60k
  # filter(Count.1 >= 1440 & Count.1 <= 60000)
  # high_max10k
  # filter(Count.1 >= 1440 & Count.1 <= 10000)
  # medium (>1/h but <1/min) corresponds to the yellow class in [1, Figure 5]
  # filter(Count.1 >= 24 & Count.1 <= 1440)
  # few (<=1/h) corresponds to the green class in [1, Figure 5]
  # filter(Count.1 <= 24)
  # few_min5
  # filter(Count.1 >= 5 & Count.1 <= 24)
count(filtered)

# Sample Functions ---------------------------
# Choose ~19% of the 528 functions in the very_high invocation class
# and look into two time spans per function (i.e., 200 plots in total)
numSamples <- 100
samplingRate <- numSamples / count(filtered)
set.seed(123)
sampled <- filtered %>%
  sample_n(numSamples)

# Plot Traces ---------------------------

plot_trace <- function(data, baseDir, variant) {
  file <- paste(baseDir, "/invocations", variant, "-count.pdf", sep = "")
  p <- ggplot(data = data, aes(x = Time, y = Invocations, group = HashFunction)) +
    geom_line(aes(color = HashFunction)) +
    expand_limits(y = 0) +
    ggtitle(variant)
  ggsave(file, width = 15, height = 7, device = cairo_pdf(), plot = p)
}

for (i in 1:numSamples) {
  fun_trace <- sampled[i,] %>%
    pivot_longer(
      cols = !all_of(keyCols) & !starts_with("Count"),
      names_to = "Time",
      values_to = "Invocations"
    )
  # ~10am if 1.0000 corresponds to midnight
  time1 <- fun_trace %>%
    filter(Time >= 1.0600 & Time < 1.0620)
  # time1 +8 hours
  time2 <- fun_trace %>%
    filter(Time >= 1.1080 & Time < 1.1100)
  
  variant1 <- sprintf('%0.3d-time1', i)
  plot_trace(time1, baseDir, variant1)
  variant2 <- sprintf('%0.3d-time2', i)
  plot_trace(time2, baseDir, variant2)
}

# References ---------------------------
# [1] shahrad:20 "Serverless in the Wild: Characterizing and Optimizing the Serverless Workload at a Large Cloud Provider" 
