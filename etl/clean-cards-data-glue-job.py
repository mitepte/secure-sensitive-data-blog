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
tbl_name = "cards"

# S3 location for output
output_s3_path = "s3://" + args['output_s3_bucket_name'] + "/clean_cards"

print("Output s3 Path " + output_s3_path)


# Read data into a DynamicFrame using the Data Catalog metadata
cards_dyf = glueContext.create_dynamic_frame.from_catalog(database = db_name, table_name = tbl_name)

cards_dataframe = cards_dyf.toDF()

# udf returns the last 4 digits of the card and deals with variance in numeric spacing by removing whitespace
@udf(returnType=StringType())
def last_four(name):
    name = name.replace(" ", "")
    name = name[-4:]
    return name

cards_dataframe = cards_dataframe.withColumn("card_number", last_four(cards_dataframe["card_number"]))

clean_tmp_dyf = DynamicFrame.fromDF(cards_dataframe, glueContext, "clean")

glueContext.write_dynamic_frame.from_options(
       frame = clean_tmp_dyf,
       connection_type = "s3",
       connection_options = {"path": output_s3_path},
       format = "csv")

