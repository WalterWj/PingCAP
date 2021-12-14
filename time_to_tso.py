#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import time
from datetime import datetime
import sys

if len(sys.argv) == 2:
    timestr = sys.argv[1]
else:
    print("Please input time")
    sys.exit(0)

# parser time
try:
    datetime_obj = datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S.%f")
except ValueError:
    print("Error: {}".format(ValueError))
    sys.exit(0)

# init time
obj_stamp = int(
    time.mktime(datetime_obj.timetuple()) * 1000.0 +
    datetime_obj.microsecond / 1000.0)

# time: 10 to 2
bit_tamp = bin(obj_stamp)

# Complete 18 bits
bit_tamp = bit_tamp + '0' * 18

# print("{}, {}".format(obj_stamp, bit_tamp))
print("TSO: {}".format(int(bit_tamp, 2)))
