import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

export interface IAMComponentArgs {
    environment: string;
    tags: Record<string, string>;
    attachToUser?: string; // Optional: IAM user name to attach policies to
}

export class IAMComponent extends pulumi.ComponentResource {
    public readonly route53Policy: aws.iam.Policy;
    public readonly deploymentUserPolicy: aws.iam.Policy;

    constructor(name: string, args: IAMComponentArgs, opts?: pulumi.ComponentResourceOptions) {
        super("happyrobot:iam", name, {}, opts);

        // Create Route 53 policy for managing DNS records
        this.route53Policy = new aws.iam.Policy(`${name}-route53-policy`, {
            name: `${name}-route53-access`,
            description: "Policy for managing Route 53 DNS records for HappyRobot FDE",
            policy: JSON.stringify({
                Version: "2012-10-17",
                Statement: [
                    {
                        Sid: "Route53ListPermissions",
                        Effect: "Allow",
                        Action: [
                            "route53:ListHostedZones",
                            "route53:ListHostedZonesByName",
                            "route53:GetHostedZoneCount",
                            "route53:ListResourceRecordSets"
                        ],
                        Resource: "*"
                    },
                    {
                        Sid: "Route53ZonePermissions",
                        Effect: "Allow",
                        Action: [
                            "route53:GetHostedZone",
                            "route53:GetHostedZoneLimit",
                            "route53:ListTagsForResource"
                        ],
                        Resource: [
                            "arn:aws:route53:::hostedzone/*"
                        ]
                    },
                    {
                        Sid: "Route53RecordPermissions",
                        Effect: "Allow",
                        Action: [
                            "route53:ChangeResourceRecordSets",
                            "route53:GetChange"
                        ],
                        Resource: [
                            "arn:aws:route53:::hostedzone/*",
                            "arn:aws:route53:::change/*"
                        ]
                    }
                ]
            }),
            tags: {
                ...args.tags,
                Name: `${name}-route53-policy`,
                Purpose: "Route53 DNS Management"
            }
        }, { parent: this });

        // Create a comprehensive deployment policy for CI/CD
        // This policy includes all permissions needed for Pulumi deployments
        this.deploymentUserPolicy = new aws.iam.Policy(`${name}-deployment-policy`, {
            name: `${name}-pulumi-deployment`,
            description: "Comprehensive policy for Pulumi deployments including Route 53",
            policy: JSON.stringify({
                Version: "2012-10-17",
                Statement: [
                    // Route 53 permissions (same as above)
                    {
                        Sid: "Route53FullAccess",
                        Effect: "Allow",
                        Action: [
                            "route53:*"
                        ],
                        Resource: "*"
                    },
                    // Add other necessary permissions that might be missing
                    {
                        Sid: "TaggingPermissions",
                        Effect: "Allow",
                        Action: [
                            "tag:GetResources",
                            "tag:TagResources",
                            "tag:UntagResources",
                            "tag:GetTagKeys",
                            "tag:GetTagValues"
                        ],
                        Resource: "*"
                    }
                ]
            }),
            tags: {
                ...args.tags,
                Name: `${name}-deployment-policy`,
                Purpose: "Pulumi CI/CD Deployment"
            }
        }, { parent: this });

        // Optionally attach policies to an existing IAM user
        if (args.attachToUser) {
            // Attach Route 53 policy to the user
            new aws.iam.UserPolicyAttachment(`${name}-user-route53-attachment`, {
                user: args.attachToUser,
                policyArn: this.route53Policy.arn,
            }, { parent: this });

            // Attach deployment policy to the user
            new aws.iam.UserPolicyAttachment(`${name}-user-deployment-attachment`, {
                user: args.attachToUser,
                policyArn: this.deploymentUserPolicy.arn,
            }, { parent: this });

            pulumi.log.info(`IAM policies will be attached to user: ${args.attachToUser}`);
        } else {
            pulumi.log.info("IAM policies created but not attached to any user. Attach manually or set 'attachToUser' parameter.");
        }

        // Export policy ARNs for manual attachment or reference
        this.registerOutputs({
            route53PolicyArn: this.route53Policy.arn,
            deploymentPolicyArn: this.deploymentUserPolicy.arn,
        });
    }
}
