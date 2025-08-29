import * as aws from '@pulumi/aws';
import * as pulumi from '@pulumi/pulumi';

interface HappyRobotDNSArgs {
    albDnsName: pulumi.Input<string>;
    albZoneId: pulumi.Input<string>;
    domainName: pulumi.Input<string>;
    environment: pulumi.Input<string>;
    commonTags: pulumi.Input<{[key: string]: pulumi.Input<string>}>;
    hostedZoneId?: pulumi.Input<string>;
}

export class HappyRobotDNS extends pulumi.ComponentResource {
    public readonly apiRecord: aws.route53.Record;

    constructor(name: string, private args: HappyRobotDNSArgs, opts?: pulumi.ResourceOptions) {
        super('happyrobot:dns:Route53', name, args, opts);

        // Defer the hosted zone lookup to deployment time
        const zoneId = pulumi.output(args.hostedZoneId).apply(zoneId => {
            if (zoneId) {
                return zoneId;
            }

            // If no zone ID provided, look up the hosted zone
            return aws.route53.getZone({
                name: 'bizai.es',
            }, { parent: this }).then(zone => zone.zoneId);
        });

        // Create an A record (ALIAS) for api.bizai.es that points to the ALB
        // Note: Route53 records don't support tags
        this.apiRecord = new aws.route53.Record(`${name}-api-record`, {
            zoneId: zoneId,
            name: args.domainName,
            type: 'A',
            aliases: [{
                name: args.albDnsName,
                zoneId: args.albZoneId,
                evaluateTargetHealth: true,
            }],
        }, { parent: this });

        // Export the created DNS record
        this.registerOutputs({
            apiRecordName: this.apiRecord.name,
            apiRecordFqdn: this.apiRecord.fqdn,
        });
    }
}
