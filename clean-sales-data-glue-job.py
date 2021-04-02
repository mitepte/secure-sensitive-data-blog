import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

glueContext = GlueContext(SparkContext.getOrCreate())

args = getResolvedOptions(sys.argv,
                          ['JOB_NAME',
                           'output_s3_bucket_name'])

# Data Catalog: database and table name
db_name = "db1"
tbl_name = "sales"

# S3 location for output
output_s3_path = "s3://" + args['output_s3_bucket_name'] + "/clean_sales"

print("Output s3 Path " + output_s3_path)

# Read data into a DynamicFrame using the Data Catalog metadata
sales_dyf = glueContext.create_dynamic_frame.from_catalog(database = db_name, table_name = tbl_name)

sales_dataframe = sales_dyf.toDF()

# udf returns the value by removing the currency char
@udf(returnType=StringType())
def remove_currency(price):
    price = price.replace("$", "")
    return price

final_dataframe = sales_dataframe.withColumn("price", remove_currency(sales_dataframe["price"]))

clean_tmp_dyf = DynamicFrame.fromDF(final_dataframe, glueContext, "clean")

final_dyf = clean_tmp_dyf.apply_mapping([('card_id', 'bigint', 'card_id', 'bigint'),
                 ('customer_id', 'bigint', 'customer_id', 'bigint'),
                 ('provider name', 'string', 'provider.name', 'string'),
                 ('product_id', 'bigint', 'product_id', 'bigint'),
                 ('price', 'string','price', 'decimal')]);
                 
final_dyf = final_dyf.drop_fields(['provider'])
                 
final_dyf.printSchema();

glueContext.write_dynamic_frame.from_options(
       frame = final_dyf,
       connection_type = "s3",
       connection_options = {"path": output_s3_path},
       format = "csv")
