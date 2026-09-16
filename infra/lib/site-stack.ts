import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as targets from 'aws-cdk-lib/aws-route53-targets';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';

export interface SiteStackProps extends cdk.StackProps {
  readonly domainName: string;
  readonly parentDomainName: string;
  readonly apiGatewayDomain?: string;
}

export class SiteStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: SiteStackProps) {
    super(scope, id, {
      ...props,
      env: { ...props.env, region: 'us-east-1' },
      description: `Site infrastructure for ${props.domainName}`,
    });

    const { domainName, parentDomainName, apiGatewayDomain } = props;
    const slug = domainName.split('.')[0];

    const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
      domainName: parentDomainName,
    });

    const table = new dynamodb.Table(this, 'SiteTable', {
      tableName: `${slug}-table`,
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      timeToLiveAttribute: 'expiresAt',
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: true },
    });

    const siteBucket = new s3.Bucket(this, 'SiteBucket', {
      bucketName: `${domainName}-site-${this.account}-${this.region}`,
      publicReadAccess: false,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
    });

    const mediaBucket = new s3.Bucket(this, 'MediaBucket', {
      bucketName: `${domainName}-media-${this.account}-${this.region}`,
      publicReadAccess: false,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      cors: [
        {
          allowedMethods: [s3.HttpMethods.PUT],
          allowedOrigins: [`https://${domainName}`],
          allowedHeaders: ['*'],
        },
      ],
    });

    const certificate = new acm.Certificate(this, 'SiteCertificate', {
      domainName: domainName,
      validation: acm.CertificateValidation.fromDns(hostedZone),
    });

    // Uploaded media: the load-bearing header is `nosniff`, which stops a
    // browser from content-sniffing an uploaded image as HTML/JS. Also framed-
    // out and given a locked-down CSP so a served object can't act as a page.
    const mediaSecurityHeaders = new cloudfront.ResponseHeadersPolicy(this, 'MediaSecurityHeaders', {
      responseHeadersPolicyName: `${slug}-media-security-headers`,
      securityHeadersBehavior: {
        contentSecurityPolicy: { override: true, contentSecurityPolicy: "default-src 'none'" },
        contentTypeOptions: { override: true },
        frameOptions: { override: true, frameOption: cloudfront.HeadersFrameOption.DENY },
      },
    });

    const mediaBehavior: cloudfront.BehaviorOptions = {
      origin: origins.S3BucketOrigin.withOriginAccessControl(mediaBucket),
      viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
      allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
      compress: true,
      cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
      responseHeadersPolicy: mediaSecurityHeaders,
    };
    const additionalBehaviors: Record<string, cloudfront.BehaviorOptions> = {
      '/media/*': mediaBehavior,
      '/message-photos/*': mediaBehavior,
    };

    if (apiGatewayDomain) {
      additionalBehaviors['/api/*'] = {
        origin: new origins.HttpOrigin(apiGatewayDomain, {
          originPath: '/Prod',
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
        cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
        originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
      };
    }

    // Security response headers for the site (HTML/JS/CSS). The CSP keeps
    // 'unsafe-inline' for script/style because SvelteKit's static adapter emits
    // inline hydration scripts; it still constrains object/base/frame-ancestors/
    // form-action. Sites that load a third-party script (a hosted sign-in
    // widget, say) add its origins to script-src/connect-src/frame-src here.
    const securityHeaders = new cloudfront.ResponseHeadersPolicy(this, 'SecurityHeadersPolicy', {
      responseHeadersPolicyName: `${slug}-security-headers`,
      securityHeadersBehavior: {
        contentSecurityPolicy: {
          override: true,
          contentSecurityPolicy: [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: blob:",
            "media-src 'self' blob:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-src 'none'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "object-src 'none'",
            "form-action 'self'",
          ].join('; '),
        },
        strictTransportSecurity: {
          override: true,
          accessControlMaxAge: cdk.Duration.days(365),
          includeSubdomains: true,
          preload: false,
        },
        contentTypeOptions: { override: true },
        frameOptions: { override: true, frameOption: cloudfront.HeadersFrameOption.DENY },
        referrerPolicy: {
          override: true,
          referrerPolicy: cloudfront.HeadersReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN,
        },
      },
    });

    const distribution = new cloudfront.Distribution(this, 'SiteDistribution', {
      comment: `Site: ${domainName}`,
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(siteBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
        compress: true,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        responseHeadersPolicy: securityHeaders,
      },
      additionalBehaviors,
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100,
      certificate: certificate,
      domainNames: [domainName],
      defaultRootObject: 'index.html',
      // Only 404 is rewritten to the SPA shell. CloudFront error responses are
      // distribution-wide, so rewriting 403 would also mask legitimate 403s
      // from the /api/* behavior (e.g. failed logins). The buckets grant
      // CloudFront s3:ListBucket below so missing objects 404 instead of 403.
      errorResponses: [
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.minutes(0),
        },
      ],
      minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
    });

    for (const bucket of [siteBucket, mediaBucket]) {
      bucket.addToResourcePolicy(
        new iam.PolicyStatement({
          actions: ['s3:ListBucket'],
          resources: [bucket.bucketArn],
          principals: [new iam.ServicePrincipal('cloudfront.amazonaws.com')],
          conditions: {
            StringEquals: {
              'AWS:SourceArn': `arn:aws:cloudfront::${this.account}:distribution/${distribution.distributionId}`,
            },
          },
        })
      );
    }

    new route53.ARecord(this, 'SubdomainAliasRecord', {
      zone: hostedZone,
      recordName: domainName,
      target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(distribution)),
    });

    new cdk.CfnOutput(this, 'SiteBucketName', { value: siteBucket.bucketName });
    new cdk.CfnOutput(this, 'MediaBucketName', { value: mediaBucket.bucketName });
    new cdk.CfnOutput(this, 'DistributionId', { value: distribution.distributionId });
    new cdk.CfnOutput(this, 'DistributionDomainName', { value: distribution.distributionDomainName });
    new cdk.CfnOutput(this, 'TableName', { value: table.tableName });
    new cdk.CfnOutput(this, 'WebsiteURL', { value: `https://${domainName}` });
  }
}
