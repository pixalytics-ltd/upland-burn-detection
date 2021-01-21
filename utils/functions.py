# Number of days in month
def numberOfDays(y, m):
  leap = 0
  if y% 400 == 0:
     leap = 1
  elif y % 100 == 0:
     leap = 0
  elif y% 4 == 0:
     leap = 1
  if m==2:
     return 28 + leap
  list = [1,3,5,7,8,10,12]
  if m in list:
     return 31
  return 30
