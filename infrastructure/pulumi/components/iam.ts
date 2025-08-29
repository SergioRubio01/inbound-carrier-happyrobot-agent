import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

export interface IAMComponentArgs {
    environment: string;
    tags: Record<string, string>;
    attachToUser?: string; // Optional: IAM user name to attach policies to
}

export class IAMComponent extends pulumi.ComponentResource {
    public readonly comprehensiveDeploymentPolicy: aws.iam.UserPolicy | undefined;

    constructor(name: string, args: IAMComponentArgs, opts?: pulumi.ComponentResourceOptions) {
        super("happyrobot:iam", name, {}, opts);

        // Create a single comprehensive deployment inline policy that includes all permissions
        // This avoids the AWS limit of 10 managed policies per user
        if (args.attachToUser) {
            this.comprehensiveDeploymentPolicy = new aws.iam.UserPolicy(`${name}-comprehensive-policy`, {
                user: args.attachToUser,
                name: `${name}-comprehensive-deployment`,
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
            }, { parent: this });

            pulumi.log.info(`Comprehensive inline IAM policy attached to user: ${args.attachToUser}`);
        } else {
            this.comprehensiveDeploymentPolicy = undefined;
            pulumi.log.info("No IAM user specified. Comprehensive inline IAM policy not created.");
        }

        // Export a flag to indicate if the policy was created
        this.registerOutputs({
            policyCreated: !!this.comprehensiveDeploymentPolicy,
        });
    }
}
