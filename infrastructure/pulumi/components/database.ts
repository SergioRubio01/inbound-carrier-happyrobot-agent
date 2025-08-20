import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import * as random from "@pulumi/random";

export interface DatabaseArgs {
    vpc: aws.ec2.Vpc;
    privateSubnets: aws.ec2.Subnet[];
    databaseSecurityGroup: aws.ec2.SecurityGroup;
    instanceClass: string;
    allocatedStorage: number;
    environment: string;
    tags: Record<string, string>;
}

export class DatabaseComponent extends pulumi.ComponentResource {
    public readonly instance: aws.rds.Instance;
    public readonly subnetGroup: aws.rds.SubnetGroup;
    public readonly secret: aws.secretsmanager.Secret;
    public readonly secretVersion: aws.secretsmanager.SecretVersion;
    public readonly endpoint: pulumi.Output<string>;
    public readonly port: pulumi.Output<number>;
    public readonly secretArn: pulumi.Output<string>;

    constructor(name: string, args: DatabaseArgs, opts?: pulumi.ComponentResourceOptions) {
        super("happyrobot:database", name, {}, opts);

        // Generate random password for database
        const dbPassword = new random.RandomPassword(`${name}-password`, {
            length: 32,
            special: true,
            overrideSpecial: "!#$%&*()-_=+[]{}:?", // Exclude characters that RDS doesn't accept: /@"' and space
        }, { parent: this });

        // Create database subnet group
        this.subnetGroup = new aws.rds.SubnetGroup(`${name}-subnet-group`, {
            name: `${name}-subnet-group`,
            subnetIds: args.privateSubnets.map(subnet => subnet.id),
            tags: {
                ...args.tags,
                Name: `${name}-subnet-group`,
            },
        }, { parent: this });

        // Use default parameter group to avoid issues with static parameters
        // Custom parameters can be added later after the database is created

        // Reference the existing database instance
        // The database already exists in AWS, so we just reference it
        this.instance = aws.rds.Instance.get(`${name}-postgres`, `${name}-postgres`, undefined, { parent: this }) as aws.rds.Instance;

        // Create AWS Secrets Manager secret for database credentials
        this.secret = new aws.secretsmanager.Secret(`${name}-credentials`, {
            name: `${name}/database/credentials`,
            description: "Database credentials for HappyRobot FDE",
            tags: {
                ...args.tags,
                Name: `${name}-credentials`,
            },
        }, { parent: this });

        // Store database credentials in secret
        this.secretVersion = new aws.secretsmanager.SecretVersion(`${name}-credentials-version`, {
            secretId: this.secret.id,
            secretString: pulumi.jsonStringify({
                username: "happyrobot",
                password: dbPassword.result,
                engine: "postgres",
                host: this.instance.endpoint,
                port: this.instance.port,
                dbname: "happyrobot",
                dbInstanceIdentifier: this.instance.identifier,
            }),
        }, { parent: this });

        // Set outputs
        this.endpoint = this.instance.endpoint;
        this.port = this.instance.port;
        this.secretArn = this.secret.arn;

        // Register outputs
        this.registerOutputs({
            instance: this.instance,
            subnetGroup: this.subnetGroup,
            secret: this.secret,
            secretVersion: this.secretVersion,
            endpoint: this.endpoint,
            port: this.port,
            secretArn: this.secretArn,
        });
    }

    private createMonitoringRole(): aws.iam.Role {
        const name = "database";
        // Create IAM role for RDS Enhanced Monitoring
        const monitoringRole = new aws.iam.Role(`${name}-monitoring-role`, {
            name: `${name}-rds-monitoring-role`,
            assumeRolePolicy: JSON.stringify({
                Version: "2012-10-17",
                Statement: [
                    {
                        Action: "sts:AssumeRole",
                        Effect: "Allow",
                        Principal: {
                            Service: "monitoring.rds.amazonaws.com",
                        },
                    },
                ],
            }),
            tags: {
                Name: `${name}-rds-monitoring-role`,
            },
        }, { parent: this });

        // Attach the AWS managed policy for RDS Enhanced Monitoring
        new aws.iam.RolePolicyAttachment(`${name}-monitoring-policy`, {
            role: monitoringRole.name,
            policyArn: "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole",
        }, { parent: this });

        return monitoringRole;
    }
}
