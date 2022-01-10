library(dplyr)
library(tidyr)
library(ggplot2)

# Configure Import ---------------------------
# in [1,14]
# i <- 1:1
i <- 1
invocations.filename <- sprintf("invocations_per_function_md.anon.d%02d.csv", i)
durations.filename <- sprintf("function_durations_percentiles.anon.d%02d.csv", i)

# Import ---------------------------
# invocations <- read.csv(invocations.filename, header = TRUE)
# durations <- read.csv(durations.filename, header = TRUE)


# 24h range: [X1:X1440]
invocations <- invocations %>%
  mutate(Count = rowSums(.[5:1444]))


invocations.filtered <- invocations %>%
  filter(Trigger != "timer") %>%
  # filter(Count >= 10000 & Count <= 100000)
  # High invocations (red)
  # filter(Count >= 1440 & Count <= 10000)
  # Medium invocations (yellow)
  filter(Count >= 24 & Count <= 1440)
  # Few invocations (green)
  # filter(Count <= 24)
  # Few invocations with minimum
  # filter(Count >= 5 & Count <= 24)
  # Wide range
  # filter(Count >= 24 & Count <= 10000)

count(invocations.filtered)

# Histogram ---------------------------
# ggplot(data = invocations.filtered, aes(x = Count)) +
#   geom_histogram()

# Series Plot ---------------------------
# set.seed(123)
invocations.long <- invocations.filtered %>%
  sample_n(5) %>%
  pivot_longer(
    cols = starts_with("X"),
    names_to = "Minute",
    names_prefix = "X",
    values_to = "Invocations"
  )

ggplot(data = invocations.long, aes(x = Minute, y = Invocations, group = HashFunction)) +
  geom_line(aes(color = HashFunction))
  # ylim(0, 10)

# 1) save to pdf
# 2) loop and re-sample to generate a series of 5-plot graphs
