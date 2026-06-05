#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { TributeSiteStack } from '../lib/site-stack';

const app = new cdk.App();

const account = process.env.CDK_DEFAULT_ACCOUNT;
const region = 'us-east-1';

if (!account) {
  throw new Error('Set CDK_DEFAULT_ACCOUNT environment variable.');
}

const siteDomain = process.env.SITE_DOMAIN;
const parentDomain = process.env.PARENT_DOMAIN;

if (!siteDomain || !parentDomain) {
  throw new Error('Set SITE_DOMAIN and PARENT_DOMAIN environment variables.');
}

const apiGatewayDomain = app.node.tryGetContext('apiGatewayDomain') as string | undefined;

new TributeSiteStack(app, 'TributeSiteStack', {
  env: { account, region },
  domainName: siteDomain,
  parentDomainName: parentDomain,
  apiGatewayDomain: apiGatewayDomain || undefined,
  tags: {
    Project: 'TributeSite',
    Environment: 'Production',
    ManagedBy: 'CDK',
  },
});

app.synth();
