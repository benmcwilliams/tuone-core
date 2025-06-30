import pandas as pd 

# read product dictionary 

df = pd.read_excel("src/product_classification.xlsx")

# compare to all products (that are used to QUANTIFY a capacity) in mongoDB
# output those products that are not yet mapped & should be 

