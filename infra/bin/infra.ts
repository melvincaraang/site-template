#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BirthdayTributeSiteStack } from '../lib/birthday-stack';

const app = new cdk.App();

const account = process.env.CDK_DEFAULT_ACCOUNT;
const region = 'us-east-1';

if (!account) {
  throw new Error('Set CDK_DEFAULT_ACCOUNT environment variable.');
}

new BirthdayTributeSiteStack(app, 'DadBirthdayStack', {
  env: { account, region },
  domainName: 'dad.melvinit.com',
  parentDomainName: 'melvinit.com',
  tags: {
    Project: 'DadBirthday',
    Environment: 'Production',
    ManagedBy: 'CDK',
  },
});

app.synth();
