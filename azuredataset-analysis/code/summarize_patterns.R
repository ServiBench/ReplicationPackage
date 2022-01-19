library(tidyverse)

# This script computes summary statistics grouped and merges the traces with the invocation pattern classification.

# sampled is created in 03_plot_invocations.R
patterns <- sampled %>%
  select(HashFunction, Trigger, Count.1) %>%
  mutate(rps = Count.1 / (1440*60)) %>%
  mutate(id = row_number())

classifications <- read.csv(file = '../results/invocations/20min_min1rps/trace_classification.csv')

numMinutes = 20
startTime = 1.0600
endTime <- startTime + numMinutes / 10000
stages <- sampled %>%
  pivot_longer(
    cols = !all_of(keyCols) & !starts_with("Count"),
    names_to = "Time",
    values_to = "InvocationsPerMinute"
  ) %>%
  filter(Time >= startTime & Time < endTime) %>%
  select(HashFunction,InvocationsPerMinute) %>%
  group_by(HashFunction) %>%
  summarise(num_invocations = sum(InvocationsPerMinute)) %>%
  mutate(rps = num_invocations / (20*60)) %>%
  mutate(id = row_number())

together <- inner_join(stages, classifications, by = c('HashFunction' = 'HashFunction'))
