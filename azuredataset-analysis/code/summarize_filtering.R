library(tidyverse)
# Summary Statistics of filtering process
# Usage: 1) Run 02_merge_2weeks.R import first

# Calculate the total number of distinct functions in the dataset using an outer join
# as certain functions might not be available over the entire 2 weeks.
# The goal is to discard temporary "toy" applications that might only be deployed for a short time.
all.outerJoin <- Reduce(function(x, y) merge(select(x, keyCols), select(y, keyCols), by = keyCols, all = TRUE), days)
count.total <- count(all.outerJoin)
# print('Total number of distinct functions in the dataset')
# print(count.total) # 74347

count.available <- count(all)
# print('Available over 2 weeks (available)')
# print(count.available) # 28783

count.noTimer <- count(all %>% filter(Trigger != "timer"))
# print('available + no timer')
# print(count.noTimer) # 13464

count.reqRate <- count(all %>% filter(Trigger != "timer") %>% filter(Count.1 >= 1440*60))
# print('available + no timer + average invocation rate >= 1 req/s')
# print(count.reqRate) # 528

glue::glue(
  "{count.total}\t Total number of distinct functions in the dataset\n",
  "-{count.total - count.available}\t Removed temporary functions\n",
  "{count.available}\t Available over 2 weeks\n",
  "-{count.available - count.noTimer}\t Removed timer triggers\n",
  "{count.noTimer}\t Available over 2 weeks AND not triggered by a timer\n",
  "-{count.noTimer - count.reqRate}\t Removed low request rates\n",
  "{count.reqRate}\t Available over 2 weeks AND not triggered by a timer AND invocations rate >= 1 request/second\n",
)
