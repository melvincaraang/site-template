import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
export interface BirthdayTributeSiteStackProps extends cdk.StackProps {
    readonly domainName: string;
    readonly parentDomainName: string;
    readonly apiGatewayDomain?: string;
}
export declare class BirthdayTributeSiteStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: BirthdayTributeSiteStackProps);
}
