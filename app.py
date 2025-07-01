#!/usr/bin/env python3
import aws_cdk as cdk
from outreach_agent.outreach_agent_stack import OutreachAgentStack

app = cdk.App()
OutreachAgentStack(app, "OutreachAgentStack")
app.synth()
