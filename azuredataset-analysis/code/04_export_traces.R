library(data.table)
library(dplyr)

# NOTE: For deriving more realistic sub-minute inter-arrival times,
# we could offer a version of this function that supports applies a
# noise function and outputs finer-grained inter-arrival times at the
# level of seconds or milliseconds.
export_trace <- function(functionHash, file, startTime = 1.0600, numMinutes = 20, scalingFactor = 1) {
  # Filter
  fun <- all[HashFunction == functionHash]
  endTime <- startTime + numMinutes / 10000
  stages <- fun %>%
    pivot_longer(
      cols = !all_of(keyCols) & !starts_with("Count"),
      names_to = "Time",
      values_to = "InvocationsPerMinute"
    ) %>%
    filter(Time >= startTime & Time < endTime) %>%
    select(InvocationsPerMinute) %>%
    mutate(InvocationsPerMinute = round(InvocationsPerMinute * scalingFactor))
  # Write CSV of invocations per minute
  write.table(stages, file, row.names = FALSE, col.names = TRUE)
}

# Configuration ---------------------------
# Trace examples
# 023-time2
constant <- '13ab342fab4291483c11b70f320f829aa12e75bd19e4abb955f7e6f0a6ef629a'
# 087-time2
bursty <- '58b091f52fac05fac5536d6f7b2a26ddecc39933061a812202c68b22622adf7c'
# 034-time1
spikes <- '02783877a12468a4fcb9140ed732dd443dac2722ebf8d4a1965dc9e0f04c13e1'
# 007-time1
jump <- '0d82a08ef7b0ee97684b504d8ecc22308d43a299d8bd823eb38e55b2b4830cf1'

# Time
time1 <- 1.0600
time2 <- 1.1080
minutes <- 20

# Destination
baseDir <- "../results/traces/20min_very_high"
dir.create(baseDir, showWarnings = FALSE)

# Variants
constant.file <- paste(baseDir, "/constant.csv", sep = '')
export_trace(constant, constant.file, time1, minutes)

bursty.file <- paste(baseDir, "/bursty.csv", sep = '')
export_trace(bursty, bursty.file, time1, minutes)

spikes.file <- paste(baseDir, "/spikes.csv", sep = '')
export_trace(spikes, spikes.file, time1, minutes)

jump.file <- paste(baseDir, "/jump.csv", sep = '')
export_trace(jump, jump.file, time1, minutes)
