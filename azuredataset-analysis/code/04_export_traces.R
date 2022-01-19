library(data.table)
library(dplyr)

# This script exports selected traces as input for load generation with sb.

# Export Destination ----------------------
baseDir <- "../results/traces/20min_picks"
dir.create(baseDir, recursive = TRUE, showWarnings = FALSE)

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

# Export Configuration ---------------------------

### Trace selection used in the paper
# 2022-01-06 Select higher rps for steady + fluctuating
# 043-time2
steady <- '2c5d363481a100391a50d5397fece786de8d4b86fc02c8880a78bcfa7b297139'
# 009-time1
fluctuating <- '08f7ff6d9380a3c0442130789c39c3006b6648ba613a3cc9f34de200ae2ee057'
# 034-time1
spikes <- '02783877a12468a4fcb9140ed732dd443dac2722ebf8d4a1965dc9e0f04c13e1'
# 007-time1
jump <- '0d82a08ef7b0ee97684b504d8ecc22308d43a299d8bd823eb38e55b2b4830cf1'

# Time
time1 <- 1.0600
time2 <- 1.1080
minutes <- 20

# Export selected traces
steady.file <- paste(baseDir, "/steady.csv", sep = '')
export_trace(steady, steady.file, time2, minutes)

fluctuating.file <- paste(baseDir, "/fluctuating.csv", sep = '')
export_trace(fluctuating, fluctuating.file, time1, minutes)

spikes.file <- paste(baseDir, "/spikes.csv", sep = '')
export_trace(spikes, spikes.file, time1, minutes)

jump.file <- paste(baseDir, "/jump.csv", sep = '')
export_trace(jump, jump.file, time1, minutes)


# Alternative Trace Selections ------------------------------

# # 4h invocations16-count.pdf blue
# spikes_4h = 'cd582a3c396b3676f15c32479b57c7959f3993e50feca3591cb1f30d05d5c385'
# # 1h very_high_cmp invocations8-count.pdf green
# fluctuating_1h = '6590c82e22abcdaf4887f5e84c39b3d264276cb7fb5bd585cdde6e8966a58966'
# 
# # file <- paste(baseDir, "/spikes_4h.csv", sep = '')
# export_trace(spikes_4h, file, time1, minutes)
# # file <- paste(baseDir, "/fluctuating_1h.csv", sep = '')
# export_trace(fluctuating_1h, file, time1, minutes)
# 
# # Trace examples
# # 023-time2
# steady <- '13ab342fab4291483c11b70f320f829aa12e75bd19e4abb955f7e6f0a6ef629a'
# # 087-time2
# fluctuating <- '58b091f52fac05fac5536d6f7b2a26ddecc39933061a812202c68b22622adf7c'
# # 034-time1
# spikes <- '02783877a12468a4fcb9140ed732dd443dac2722ebf8d4a1965dc9e0f04c13e1'
# # 007-time1
# jump <- '0d82a08ef7b0ee97684b504d8ecc22308d43a299d8bd823eb38e55b2b4830cf1'
# 
# # Selected for around 18-20rps
# jump = '295ed129ebf7fab6ade6ae2c4bf15a91d84d607553e21950bf5b7b4a47411a48'
# #079-time1
# steady = '295ed129ebf7fab6ade6ae2c4bf15a91d84d607553e21950bf5b7b4a47411a48'
# #079-time2
# spikes = '52df3473cd810e5d9eb4923260c0189b6136da3193253f984fb97bca8e8b3deb'
# #057-time1
# fluctuating = '52df3473cd810e5d9eb4923260c0189b6136da3193253f984fb97bca8e8b3deb'
# #057-time2

