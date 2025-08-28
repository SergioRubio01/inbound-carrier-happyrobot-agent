import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

export interface IAMComponentArgs {
    environment: string;
    tags: Record<string, string>;
    attachToUser?: string; // Optional: IAM user name to attach policies to
}

export class IAMComponent extends pulumi.ComponentResource {
    public readonly comprehensiveDeploymentPolicy: aws.iam.Policy;

    constructor(name: string, args: IAMComponentArgs, opts?: pulumi.ComponentResourceOptions) {
        super("happyrobot:iam", name, {}, opts);

        // Create a single comprehensive deployment policy that includes all permissions
        // This consolidation helps avoid the AWS limit of 10 policies per user
        this.comprehensiveDeploymentPolicy = new aws.iam.Policy(`${name}-comprehensive-policy`, {
            name: `${name}-comprehensive-deployment`,
            description: "Comprehensive policy for Pulumi deployments including Route 53 and all deployment permissions",
            policy: JSON.stringify({
                Version: "2012-10-17",
                Statement: [
                    // Route 53 List permissions (needed for getZone operations)
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
                    // Route 53 Zone permissions
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
                    // Route 53 Record permissions
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
                    },
                    // Tagging permissions
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
                Name: `${name}-comprehensive-policy`,
                Purpose: "Comprehensive Pulumi Deployment"
            }
        }, { parent: this });

        // Optionally attach the comprehensive policy to an existing IAM user
        if (args.attachToUser) {
            // Attach the single comprehensive policy to the user
            new aws.iam.UserPolicyAttachment(`${name}-user-comprehensive-attachment`, {
                user: args.attachToUser,
                policyArn: this.comprehensiveDeploymentPolicy.arn,
            }, { parent: this });

            pulumi.log.info(`Comprehensive IAM policy will be attached to user: ${args.attachToUser}`);
        } else {
            pulumi.log.info("Comprehensive IAM policy created but not attached to any user. Attach manually or set 'attachToUser' parameter.");
        }

        // Export policy ARN for manual attachment or reference
        this.registerOutputs({
            comprehensivePolicyArn: this.comprehensiveDeploymentPolicy.arn,
        });
    }
}
