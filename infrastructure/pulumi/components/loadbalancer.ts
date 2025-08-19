import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

export interface LoadBalancerArgs {
    vpc: aws.ec2.Vpc;
    publicSubnets: aws.ec2.Subnet[];
    albSecurityGroup: aws.ec2.SecurityGroup;
    apiTargetGroup: aws.lb.TargetGroup;
    certificateArn?: string;
    environment: string;
    tags: Record<string, string>;
}

export class LoadBalancerComponent extends pulumi.ComponentResource {
    public readonly alb: aws.lb.LoadBalancer;
    public readonly httpListener: aws.lb.Listener;
    public readonly httpsListener?: aws.lb.Listener;
    public readonly apiListenerRule: aws.lb.ListenerRule;

    constructor(name: string, args: LoadBalancerArgs, opts?: pulumi.ComponentResourceOptions) {
        super("happyrobot:loadbalancer", name, {}, opts);

        // Create Application Load Balancer
        this.alb = new aws.lb.LoadBalancer(`${name}-alb`, {
            name: `${name}-alb`,
            loadBalancerType: "application",
            internal: false,
            securityGroups: [args.albSecurityGroup.id],
            subnets: args.publicSubnets.map(subnet => subnet.id),

            enableDeletionProtection: args.environment === "prod",
            enableHttp2: true,
            enableCrossZoneLoadBalancing: true,

            accessLogs: {
                bucket: this.createAccessLogsBucket(args).bucket,
                enabled: true,
                prefix: "alb-access-logs",
            },

            tags: {
                ...args.tags,
                Name: `${name}-alb`,
            },
        }, { parent: this });

        // Create HTTP listener (redirects to HTTPS if certificate is provided)
        this.httpListener = new aws.lb.Listener(`${name}-http-listener`, {
            loadBalancerArn: this.alb.arn,
            port: "80",
            protocol: "HTTP",

            defaultActions: args.certificateArn ? [
                {
                    type: "redirect",
                    redirect: {
                        port: "443",
                        protocol: "HTTPS",
                        statusCode: "HTTP_301",
                    },
                },
            ] : [
                {
                    type: "forward",
                    targetGroupArn: args.apiTargetGroup.arn,
                },
            ],

            tags: {
                ...args.tags,
                Name: `${name}-http-listener`,
            },
        }, { parent: this });

        // Create HTTPS listener if certificate is provided
        if (args.certificateArn) {
            this.httpsListener = new aws.lb.Listener(`${name}-https-listener`, {
                loadBalancerArn: this.alb.arn,
                port: "443",
                protocol: "HTTPS",
                sslPolicy: "ELBSecurityPolicy-TLS-1-2-2017-01",
                certificateArn: args.certificateArn,

                defaultActions: [
                    {
                        type: "forward",
                        targetGroupArn: args.apiTargetGroup.arn,
                    },
                ],

                tags: {
                    ...args.tags,
                    Name: `${name}-https-listener`,
                },
            }, { parent: this });
        }

        // Determine which listener to use for rules
        const listenerArn = this.httpsListener ? this.httpsListener.arn : this.httpListener.arn;

        // Create listener rule for API routes (/api/*)
        this.apiListenerRule = new aws.lb.ListenerRule(`${name}-api-rule`, {
            listenerArn: listenerArn,
            priority: 100,

            actions: [
                {
                    type: "forward",
                    targetGroupArn: args.apiTargetGroup.arn,
                },
            ],

            conditions: [
                {
                    pathPattern: {
                        values: ["/api/*"],
                    },
                },
            ],

            tags: {
                ...args.tags,
                Name: `${name}-api-rule`,
            },
        }, { parent: this });

        // Create listener rule for health check
        new aws.lb.ListenerRule(`${name}-health-rule`, {
            listenerArn: listenerArn,
            priority: 90,

            actions: [
                {
                    type: "forward",
                    targetGroupArn: args.apiTargetGroup.arn,
                },
            ],

            conditions: [
                {
                    pathPattern: {
                        values: ["/health", "/api/v1/health"],
                    },
                },
            ],

            tags: {
                ...args.tags,
                Name: `${name}-health-rule`,
            },
        }, { parent: this });

        // Create listener rule for API documentation
        new aws.lb.ListenerRule(`${name}-docs-rule`, {
            listenerArn: listenerArn,
            priority: 95,

            actions: [
                {
                    type: "forward",
                    targetGroupArn: args.apiTargetGroup.arn,
                },
            ],

            conditions: [
                {
                    pathPattern: {
                        values: ["/docs*", "/redoc*", "/openapi.json"],
                    },
                },
            ],

            tags: {
                ...args.tags,
                Name: `${name}-docs-rule`,
            },
        }, { parent: this });


        // Create WAF for additional security (optional for POC)
        if (args.environment === "prod") {
            this.createWAF(args);
        }

        // Register outputs
        this.registerOutputs({
            alb: this.alb,
            httpListener: this.httpListener,
            httpsListener: this.httpsListener,
            apiListenerRule: this.apiListenerRule,
        });
    }

    private createAccessLogsBucket(args: LoadBalancerArgs): aws.s3.Bucket {
        // Create S3 bucket for ALB access logs
        const bucket = new aws.s3.Bucket(`${this.getResource().urn.name}-access-logs`, {
            bucket: `${this.getResource().urn.name}-alb-access-logs-${args.environment}`,

            versioning: {
                enabled: false,
            },

            lifecycleRules: [
                {
                    id: "delete-old-logs",
                    enabled: true,
                    expiration: {
                        days: args.environment === "prod" ? 90 : 30,
                    },
                },
            ],

            serverSideEncryptionConfiguration: {
                rule: {
                    applyServerSideEncryptionByDefault: {
                        sseAlgorithm: "AES256",
                    },
                },
            },

            publicAccessBlock: {
                blockPublicAcls: true,
                blockPublicPolicy: true,
                ignorePublicAcls: true,
                restrictPublicBuckets: true,
            },

            tags: {
                ...args.tags,
                Name: `${this.getResource().urn.name}-access-logs`,
                Purpose: "ALB Access Logs",
            },
        }, { parent: this });

        // Get the current AWS region and account ID for the bucket policy
        const current = aws.getCallerIdentity({});
        const region = aws.getRegion({});

        // Create bucket policy to allow ALB to write logs
        new aws.s3.BucketPolicy(`${this.getResource().urn.name}-access-logs-policy`, {
            bucket: bucket.id,
            policy: pulumi.all([current, region, bucket.arn]).apply(([account, reg, bucketArn]) => {
                // ELB service account IDs by region
                const elbServiceAccounts: { [key: string]: string } = {
                    "us-east-1": "127311923021",
                    "us-east-2": "033677994240",
                    "us-west-1": "027434742980",
                    "us-west-2": "797873946194",
                    "eu-west-1": "156460612806",
                    "eu-west-2": "652711504416",
                    "eu-west-3": "009996457667",
                    "eu-central-1": "054676820928",
                    "eu-south-1": "635631232127",
                    "eu-south-2": "975236955715", // Spain region
                    "ap-northeast-1": "582318560864",
                    "ap-northeast-2": "600734575887",
                    "ap-southeast-1": "114774131450",
                    "ap-southeast-2": "783225319266",
                    "ap-south-1": "718504428378",
                    "sa-east-1": "507241528517",
                    "ca-central-1": "985666609251",
                };

                const elbServiceAccount = elbServiceAccounts[reg.name] || elbServiceAccounts["us-east-1"];

                return JSON.stringify({
                    Version: "2012-10-17",
                    Statement: [
                        {
                            Effect: "Allow",
                            Principal: {
                                AWS: `arn:aws:iam::${elbServiceAccount}:root`,
                            },
                            Action: "s3:PutObject",
                            Resource: `${bucketArn}/alb-access-logs/AWSLogs/${account.accountId}/*`,
                        },
                        {
                            Effect: "Allow",
                            Principal: {
                                Service: "delivery.logs.amazonaws.com",
                            },
                            Action: "s3:PutObject",
                            Resource: `${bucketArn}/alb-access-logs/AWSLogs/${account.accountId}/*`,
                            Condition: {
                                StringEquals: {
                                    "s3:x-amz-acl": "bucket-owner-full-control",
                                },
                            },
                        },
                        {
                            Effect: "Allow",
                            Principal: {
                                Service: "delivery.logs.amazonaws.com",
                            },
                            Action: "s3:GetBucketAcl",
                            Resource: bucketArn,
                        },
                    ],
                });
            }),
        }, { parent: this });

        return bucket;
    }

    private createWAF(args: LoadBalancerArgs) {
        // Create WAF Web ACL for production environments
        const webAcl = new aws.wafv2.WebAcl(`${this.getResource().urn.name}-waf`, {
            name: `${this.getResource().urn.name}-waf`,
            description: "WAF for HappyRobot FDE ALB",
            scope: "REGIONAL",

            defaultAction: {
                allow: {},
            },

            rules: [
                {
                    name: "AWSManagedRulesCommonRuleSet",
                    priority: 1,
                    statement: {
                        managedRuleGroupStatement: {
                            name: "AWSManagedRulesCommonRuleSet",
                            vendorName: "AWS",
                        },
                    },
                    visibilityConfig: {
                        sampledRequestsEnabled: true,
                        cloudwatchMetricsEnabled: true,
                        metricName: "CommonRuleSetMetric",
                    },
                    overrideAction: {
                        none: {},
                    },
                },
                {
                    name: "AWSManagedRulesKnownBadInputsRuleSet",
                    priority: 2,
                    statement: {
                        managedRuleGroupStatement: {
                            name: "AWSManagedRulesKnownBadInputsRuleSet",
                            vendorName: "AWS",
                        },
                    },
                    visibilityConfig: {
                        sampledRequestsEnabled: true,
                        cloudwatchMetricsEnabled: true,
                        metricName: "KnownBadInputsMetric",
                    },
                    overrideAction: {
                        none: {},
                    },
                },
                {
                    name: "RateLimitRule",
                    priority: 3,
                    statement: {
                        rateBasedStatement: {
                            limit: 1000,
                            aggregateKeyType: "IP",
                        },
                    },
                    action: {
                        block: {},
                    },
                    visibilityConfig: {
                        sampledRequestsEnabled: true,
                        cloudwatchMetricsEnabled: true,
                        metricName: "RateLimitMetric",
                    },
                },
            ],

            visibilityConfig: {
                sampledRequestsEnabled: true,
                cloudwatchMetricsEnabled: true,
                metricName: `${this.getResource().urn.name}-waf-metric`,
            },

            tags: {
                ...args.tags,
                Name: `${this.getResource().urn.name}-waf`,
            },
        }, { parent: this });

        // Associate WAF with ALB
        new aws.wafv2.WebAclAssociation(`${this.getResource().urn.name}-waf-association`, {
            resourceArn: this.alb.arn,
            webAclArn: webAcl.arn,
        }, { parent: this });
    }
}
