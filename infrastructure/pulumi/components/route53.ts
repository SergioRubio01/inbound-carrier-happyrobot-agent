import * as aws from '@pulumi/aws';
import * as pulumi from '@pulumi/pulumi';

interface HappyRobotDNSArgs {
    albDnsName: pulumi.Input<string>;
    albZoneId: pulumi.Input<string>;
    domainName: pulumi.Input<string>;
    environment: pulumi.Input<string>;
    commonTags: pulumi.Input<{[key: string]: pulumi.Input<string>}>;
}

export class HappyRobotDNS extends pulumi.ComponentResource {
    public readonly apiRecord: aws.route53.Record;

    constructor(name: string, private args: HappyRobotDNSArgs, opts?: pulumi.ResourceOptions) {
        super('happyrobot:dns:Route53', name, args, opts);

        // Look up the existing hosted zone for bizai.es domain
        const hostedZone = aws.route53.getZone({
            name: 'bizai.es',
        }, { parent: this });

        // Create an A record (ALIAS) for api.bizai.es that points to the ALB
        this.apiRecord = new aws.route53.Record(`${name}-api-record`, {
            zoneId: hostedZone.then(zone => zone.zoneId),
            name: args.domainName,
            type: 'A',
            aliases: [{
                name: args.albDnsName,
                zoneId: args.albZoneId,
                evaluateTargetHealth: true,
            }],
            tags: {
                ...args.commonTags,
                Environment: args.environment,
            },
        }, { parent: this });

        // Export the created DNS record
        this.registerOutputs({
            apiRecordName: this.apiRecord.name,
            apiRecordFqdn: this.apiRecord.fqdn,
        });
    }
}
