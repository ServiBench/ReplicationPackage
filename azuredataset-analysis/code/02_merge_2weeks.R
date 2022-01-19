library(data.table)
library(dplyr)
library(purrr)

# This script imports the 14 chunks of the original dataset and merges them
# into a single variable called `all`.

# Load Configuration ---------------------------
dataPath <- '../data'
filePattern <- 'invocations_per_function_md.anon.d[0-9][0-9].csv'
keyCols <- c('HashOwner','HashApp', 'HashFunction', 'Trigger')

# Load Functions ---------------------------
read_file <- function(file, i) {
  # Omits the 'X' prefix in column names
  d <- fread(file, header = TRUE)
  # Prefix each column with day.
  # Example 1: X1 of day1 becomes 1.0001
  # Example 2: X1440 of day 3 becomes 3.1440
  # Alternatively: Could transform into dates between 2019-07-15 till 2019-07-28
  suffix <- sprintf('%0.4d', 1:1440)
  minuteCols <- paste(i, suffix, sep = '.')
  # Suffix each Trigger column to avoid name conflicts between different days
  # NOT relevant anymore when using Trigger as additional merge key
  # triggerCol <- paste('Trigger', i, sep = ".")
  newNames <- c(keyCols, minuteCols)
  setnames(d, newNames)
  # Calculate daily invocations
  countCol <- paste('Count', i, sep = ".")
  d[, {{countCol}} := rowSums(.SD), .SDcols = 5:1444]
}

read_files <- function(path = '.', pattern = 'invocations_per_function_md.anon.d[0-9][0-9].csv') {
  list.files(path, pattern, full.names = TRUE) %>% 
    imap(read_file)
}

# Load and Merge ---------------------------
# These steps are quite memory intensive (rsession up to ~10GB)
# and can take several minutes to complete

# Large list (14 elements, 3.8 GB)
days <- read_files(dataPath, filePattern)
# 28783 obs. of 20178 variables
all <- Reduce(function(x, y) merge(x, y, by = keyCols, all = FALSE), days)
