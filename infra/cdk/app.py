"""CDK entrypoint for the media27 infrastructure.

Discovered by `cdk.json` (`app: python app.py`). Each Stack instantiated
here becomes a separate CloudFormation stack that can be deployed,
updated, and destroyed independently.
"""

from __future__ import annotations

import os

from aws_cdk import App, Environment, Tags

from stacks.api_stack import ApiStack
from stacks.data_stack import DataStack
from stacks.ingest_stack import IngestStack
from stacks.network_stack import NetworkStack

REGION = "eu-west-3"

env = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=REGION,
)

app = App()

network = NetworkStack(app, "Media27Network", env=env)

data = DataStack(
    app,
    "Media27Data",
    vpc=network.vpc,
    rds_sg=network.rds_sg,
    env=env,
)
data.add_dependency(network)

ingest = IngestStack(
    app,
    "Media27Ingest",
    vpc=network.vpc,
    lambda_vpc_sg=network.lambda_vpc_sg,
    db=data.db,
    db_secret=data.db_secret,
    env=env,
)
ingest.add_dependency(data)

api = ApiStack(
    app,
    "Media27Api",
    vpc=network.vpc,
    lambda_vpc_sg=network.lambda_vpc_sg,
    db=data.db,
    db_secret=data.db_secret,
    env=env,
)
api.add_dependency(data)

Tags.of(app).add("project", "media27")

app.synth()
