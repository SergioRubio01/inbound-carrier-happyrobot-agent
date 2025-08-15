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

        // Create database parameter group for PostgreSQL optimization
        const parameterGroup = new aws.rds.ParameterGroup(`${name}-parameter-group`, {
            family: "postgres15",
            name: `${name}-parameter-group`,
            description: "Custom parameter group for HappyRobot PostgreSQL",
            parameters: [
                {
                    name: "shared_preload_libraries",
                    value: "pg_stat_statements",
                },
                {
                    name: "log_statement",
                    value: "all",
                },
                {
                    name: "log_min_duration_statement",
                    value: "1000", // Log queries taking more than 1 second
                },
                {
                    name: "max_connections",
                    value: "200", // Match connection pool size from architecture
                },
            ],
            tags: {
                ...args.tags,
                Name: `${name}-parameter-group`,
            },
        }, { parent: this });

        // Create RDS PostgreSQL instance
        this.instance = new aws.rds.Instance(`${name}-postgres`, {
            identifier: `${name}-postgres`,
            engine: "postgres",
            engineVersion: "15.4",
            instanceClass: args.instanceClass,
            allocatedStorage: args.allocatedStorage,
            storageType: "gp3",
            storageEncrypted: true,

            // Database configuration
            dbName: "happyrobot",
            username: "happyrobot",
            password: dbPassword.result,

            // Network configuration
            dbSubnetGroupName: this.subnetGroup.name,
            vpcSecurityGroupIds: [args.databaseSecurityGroup.id],
            publiclyAccessible: false,

            // Backup and maintenance
            backupRetentionPeriod: args.environment === "prod" ? 7 : 1,
            backupWindow: "03:00-04:00", // 3-4 AM UTC
            maintenanceWindow: "Sun:04:00-Sun:05:00", // Sunday 4-5 AM UTC
            autoMinorVersionUpgrade: true,
            applyImmediately: false,

            // Performance and monitoring
            parameterGroupName: parameterGroup.name,
            performanceInsightsEnabled: true,
            performanceInsightsRetentionPeriod: 7,
            monitoringInterval: 60,
            monitoringRoleArn: this.createMonitoringRole().arn,
            enabledCloudwatchLogsExports: ["postgresql"],

            // Deletion protection for production
            deletionProtection: args.environment === "prod",
            skipFinalSnapshot: args.environment !== "prod",
            finalSnapshotIdentifier: args.environment === "prod" ? `${name}-final-snapshot` : undefined,

            tags: {
                ...args.tags,
                Name: `${name}-postgres`,
            },
        }, { parent: this });

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
        // Create IAM role for RDS Enhanced Monitoring
        const monitoringRole = new aws.iam.Role(`${this.getResource().urn.name}-monitoring-role`, {
            name: `${this.getResource().urn.name}-rds-monitoring-role`,
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
                Name: `${this.getResource().urn.name}-rds-monitoring-role`,
            },
        }, { parent: this });

        // Attach the AWS managed policy for RDS Enhanced Monitoring
        new aws.iam.RolePolicyAttachment(`${this.getResource().urn.name}-monitoring-policy`, {
            role: monitoringRole.name,
            policyArn: "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole",
        }, { parent: this });

        return monitoringRole;
    }
}
