import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

export interface LoadBalancerArgs {
    vpc: aws.ec2.Vpc;
    publicSubnets: aws.ec2.Subnet[];
    albSecurityGroup: aws.ec2.SecurityGroup;
    apiTargetGroup: aws.lb.TargetGroup;
    certificateArn?: string;
    enableHttps?: boolean; // Enable HTTPS with AWS-managed certificates
    environment: string;
    tags: Record<string, string>;
}

export class LoadBalancerComponent extends pulumi.ComponentResource {
    public readonly alb: aws.lb.LoadBalancer;
    public readonly httpListener: aws.lb.Listener;
    public readonly httpsListener?: aws.lb.Listener;
    public readonly apiListenerRule: aws.lb.ListenerRule;
    public readonly certificate?: aws.acm.Certificate;

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

            // Access logs temporarily disabled due to S3 permissions issues
            // TODO: Fix S3 bucket policy for ALB access logs
            // accessLogs: {
            //     bucket: this.createAccessLogsBucket(args).bucket,
            //     enabled: true,
            //     prefix: "alb-access-logs",
            // },

            tags: {
                ...args.tags,
                Name: `${name}-alb`,
            },
        }, { parent: this });

        // HTTPS is only enabled if a certificate ARN is provided
        // AWS ALBs require valid certificates for HTTPS listeners
        const httpsEnabled = !!args.certificateArn;
        const certificateArn = args.certificateArn;

        // Create HTTP listener (redirects to HTTPS if HTTPS is enabled)
        this.httpListener = new aws.lb.Listener(`${name}-http-listener`, {
            loadBalancerArn: this.alb.arn,
            port: 80,
            protocol: "HTTP",

            defaultActions: httpsEnabled ? [
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
        if (httpsEnabled && certificateArn) {
            // For now, use the existing listener that was manually created
            // This prevents Pulumi from trying to create a duplicate
            // TODO: Remove this workaround after properly importing the listener
            if (args.environment === "dev") {
                // Get the existing manually created listener
                this.httpsListener = aws.lb.Listener.get(`${name}-https-listener`,
                    "arn:aws:elasticloadbalancing:eu-south-2:533267139503:listener/app/happyrobot-dev-loadbalancer-alb/d734ec258e344f19/c9f87e7427a952ce",
                    undefined, { parent: this });
            } else {
                // For other environments, create normally
                this.httpsListener = new aws.lb.Listener(`${name}-https-listener`, {
                    loadBalancerArn: this.alb.arn,
                    port: 443,
                    protocol: "HTTPS",
                    sslPolicy: "ELBSecurityPolicy-TLS13-1-2-2021-06", // Use latest TLS 1.3 policy
                    certificateArn: certificateArn,
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

        // Add security header rules
        this.addSecurityHeaders(name, listenerArn, args);


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
            certificate: this.certificate,
        });
    }

    private addSecurityHeaders(name: string, listenerArn: pulumi.Output<string>, args: LoadBalancerArgs) {
        // Note: ALB cannot modify response headers directly
        // Security headers should be implemented at the application level (FastAPI middleware)
        // This is a placeholder for future security enhancements at the ALB level

        // ALB can only modify request headers and perform basic actions
        // For security headers like HSTS, CSP, etc., these must be implemented in the FastAPI application

        // TODO: Consider implementing response header modification using Lambda@Edge or CloudFront
        // For now, document that security headers are handled by the FastAPI application
    }

    private createAccessLogsBucket(args: LoadBalancerArgs): aws.s3.Bucket {
        const name = "loadbalancer";
        // Create S3 bucket for ALB access logs
        const bucket = new aws.s3.Bucket(`${name}-access-logs`, {
            bucket: `${name}-alb-access-logs-${args.environment}`,

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


            tags: {
                ...args.tags,
                Name: `${name}-access-logs`,
                Purpose: "ALB Access Logs",
            },
        }, { parent: this });

        // Get the current AWS region and account ID for the bucket policy
        const current = aws.getCallerIdentity({});
        const region = aws.getRegion({});

        // Create bucket policy to allow ALB to write logs
        new aws.s3.BucketPolicy(`${name}-access-logs-policy`, {
            bucket: bucket.id,
            policy: bucket.arn.apply((bucketArn) => {
                // Simplified policy for ALB access logs
                return JSON.stringify({
                    Version: "2012-10-17",
                    Statement: [
                        {
                            Sid: "AllowALBAccessLogs",
                            Effect: "Allow",
                            Principal: {
                                Service: "elasticloadbalancing.amazonaws.com"
                            },
                            Action: "s3:PutObject",
                            Resource: `${bucketArn}/*`
                        }
                    ],
                });
            }),
        }, { parent: this });

        return bucket;
    }

    private createWAF(args: LoadBalancerArgs) {
        const name = "loadbalancer";
        // Create WAF Web ACL for production environments
        const webAcl = new aws.wafv2.WebAcl(`${name}-waf`, {
            name: `${name}-waf`,
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
                metricName: `${name}-waf-metric`,
            },

            tags: {
                ...args.tags,
                Name: `${name}-waf`,
            },
        }, { parent: this });

        // Associate WAF with ALB
        new aws.wafv2.WebAclAssociation(`${name}-waf-association`, {
            resourceArn: this.alb.arn,
            webAclArn: webAcl.arn,
        }, { parent: this });
    }
}
