import * as cdk from 'aws-cdk-lib';
import { Annotations, Match, Template } from 'aws-cdk-lib/assertions';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';
import { SiteStack } from '../lib/site-stack';

function synth() {
  // Hosted zone lookup needs real credentials; pre-seed the context value a lookup would cache.
  const app = new cdk.App({
    context: {
      'hosted-zone:account=123456789012:domainName=example.com:region=us-east-1': {
        Id: '/hostedzone/Z123',
        Name: 'example.com.',
      },
    },
  });
  const stack = new SiteStack(app, 'test-site', {
    env: { account: '123456789012', region: 'us-east-1' },
    domainName: 'site.example.com',
    parentDomainName: 'example.com',
    apiGatewayDomain: 'abc123.execute-api.us-east-1.amazonaws.com',
  });
  return { app, stack };
}

describe('SiteStack', () => {
  test('security posture assertions', () => {
    const { stack } = synth();
    const t = Template.fromStack(stack);

    t.hasResourceProperties('AWS::S3::Bucket', {
      PublicAccessBlockConfiguration: {
        BlockPublicAcls: true,
        BlockPublicPolicy: true,
        IgnorePublicAcls: true,
        RestrictPublicBuckets: true,
      },
      BucketEncryption: Match.anyValue(),
    });
    // enforceSSL: every bucket policy must deny non-TLS requests.
    t.hasResourceProperties('AWS::S3::BucketPolicy', {
      PolicyDocument: Match.objectLike({
        Statement: Match.arrayWith([
          Match.objectLike({ Effect: 'Deny', Condition: { Bool: { 'aws:SecureTransport': 'false' } } }),
        ]),
      }),
    });
    t.hasResourceProperties('AWS::DynamoDB::Table', {
      BillingMode: 'PAY_PER_REQUEST',
      PointInTimeRecoverySpecification: { PointInTimeRecoveryEnabled: true },
      SSESpecification: { SSEEnabled: true },
    });
    t.hasResourceProperties('AWS::CloudFront::Distribution', {
      DistributionConfig: Match.objectLike({
        ViewerCertificate: Match.objectLike({ MinimumProtocolVersion: 'TLSv1.2_2021' }),
        DefaultCacheBehavior: Match.objectLike({ ViewerProtocolPolicy: 'redirect-to-https' }),
      }),
    });
    t.hasResourceProperties('AWS::CloudFront::ResponseHeadersPolicy', {
      ResponseHeadersPolicyConfig: Match.objectLike({
        SecurityHeadersConfig: Match.objectLike({
          StrictTransportSecurity: Match.objectLike({ Override: true }),
          ContentTypeOptions: { Override: true },
          FrameOptions: Match.objectLike({ FrameOption: 'DENY' }),
        }),
      }),
    });
    // Uploaded media is served with nosniff + a deny-all CSP so an upload can never act as a page.
    t.hasResourceProperties('AWS::CloudFront::ResponseHeadersPolicy', {
      ResponseHeadersPolicyConfig: Match.objectLike({
        SecurityHeadersConfig: Match.objectLike({
          ContentSecurityPolicy: Match.objectLike({ ContentSecurityPolicy: "default-src 'none'" }),
          ContentTypeOptions: { Override: true },
        }),
      }),
    });
    // /api/* must never be cached and must forward all methods.
    t.hasResourceProperties('AWS::CloudFront::Distribution', {
      DistributionConfig: Match.objectLike({
        CacheBehaviors: Match.arrayWith([
          Match.objectLike({
            PathPattern: '/api/*',
            // arrayWith matches an ordered subsequence; CloudFront lists methods in this order.
            AllowedMethods: Match.arrayWith(['PUT', 'POST', 'DELETE']),
          }),
        ]),
      }),
    });
  });

  test('cdk-nag AwsSolutions pack has no unsuppressed errors', () => {
    const { app, stack } = synth();
    cdk.Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
    NagSuppressions.addStackSuppressions(stack, [
      { id: 'AwsSolutions-S1', reason: 'Site/media buckets; access logging adds cost with no audience for the logs on a small site.' },
      { id: 'AwsSolutions-CFR1', reason: 'No geo restriction: the site is meant to be reachable worldwide.' },
      { id: 'AwsSolutions-CFR2', reason: 'WAF is out of proportion for a low-traffic personal site behind an allowlist login.' },
      { id: 'AwsSolutions-CFR3', reason: 'CloudFront access logging not needed for a personal site.' },
      { id: 'AwsSolutions-CFR7', reason: 'Origin access control is used (OAC), which supersedes OAI; rule predates OAC.' },
    ]);
    app.synth();
    const errors = Annotations.fromStack(stack).findError('*', Match.stringLikeRegexp('AwsSolutions-.*'));
    expect(errors.map((e) => `${e.id}: ${JSON.stringify(e.entry.data)}`)).toEqual([]);
  });
});
