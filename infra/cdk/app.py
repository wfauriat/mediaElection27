"""CDK entrypoint for the media27 infrastructure.

Discovered by `cdk.json` (`app: python app.py`). Each Stack instantiated
here becomes a separate CloudFormation stack that can be deployed,
updated, and destroyed independently.
"""

from __future__ import annotations

import os

from aws_cdk import App, Environment, Tags

from stacks.data_stack import DataStack
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

Tags.of(app).add("project", "media27")

app.synth()
