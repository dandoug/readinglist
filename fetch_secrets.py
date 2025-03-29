"""
This script is designed for use in the deployed AWS Elastic Beanstalk environment. 
It accesses AWS Secrets Manager to retrieve secrets and writes them to a `.env` file, 
which is then used by the application for configuration. 

The script is triggered by a command defined in the `.ebextensions` configuration files. 
In development environments, this script is not used, as a `.env` file is provided manually.
"""
import boto3
import json
import os

AWS_REGION = os.getenv("AWS_REGION")
SECRET_NAME = os.getenv("SECRET_NAME")


def fetch_secrets(secret_name):
    client = boto3.client('secretsmanager', region_name=AWS_REGION)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])


if __name__ == "__main__":
    if not SECRET_NAME:
        raise ValueError("Environment variable SECRET_NAME must be set to the name of the secret.")
    if not AWS_REGION:
        raise ValueError("Environment variable AWS_REGION must be set to the name of the region from which to retrieve the secret.")

    secrets = fetch_secrets(SECRET_NAME)

    # Write secrets to a .env file that will be loaded by app into configuration
    with open(".env", "w") as f:
        for key, value in secrets.items():
            f.write(f"{key}={value}\n")
