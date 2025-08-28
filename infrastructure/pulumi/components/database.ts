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

        // Check if we should import an existing RDS instance or create a new one
        // This allows for smooth transitions from existing infrastructure
        const importExisting = pulumi.Config.prototype.getBoolean.call(new pulumi.Config(), "importExistingDatabase") || false;

        if (importExisting) {
            // Import existing RDS instance
            this.instance = aws.rds.Instance.get(`${name}-postgres`, `${name}-postgres`, undefined, { parent: this });
        } else {
            // Create RDS parameter group for PostgreSQL optimization (only when creating new instance)
            const parameterGroup = new aws.rds.ParameterGroup(`${name}-parameter-group`, {
                name: `${name}-parameter-group`,
                family: "postgres15",
                description: "Custom parameter group for HappyRobot FDE PostgreSQL",
                parameters: [
                    {
                        name: "shared_preload_libraries",
                        value: "pg_stat_statements",
                    },
                    {
                        name: "log_statement",
                        value: "all",
                    },
                ],
                tags: {
                    ...args.tags,
                    Name: `${name}-parameter-group`,
                },
            }, { parent: this });

            // Create new RDS instance
            this.instance = new aws.rds.Instance(`${name}-postgres`, {
                identifier: `${name}-postgres`,
                engine: "postgres",
                engineVersion: "15.8", // Latest stable PostgreSQL 15.x version
                instanceClass: args.instanceClass,
                allocatedStorage: args.allocatedStorage,
                maxAllocatedStorage: args.allocatedStorage * 2, // Allow auto-scaling up to 2x initial storage
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
                backupRetentionPeriod: 7,
                backupWindow: "03:00-04:00", // UTC
                maintenanceWindow: "sun:04:00-sun:05:00", // UTC

                // Monitoring and logging
                enabledCloudwatchLogsExports: ["postgresql"],
                performanceInsightsEnabled: true,
                performanceInsightsRetentionPeriod: 7, // Free tier
                monitoringInterval: 60, // Enhanced monitoring every 60 seconds
                monitoringRoleArn: this.createMonitoringRole().arn,

                // High availability and performance
                multiAz: false, // Disabled to reduce costs
                parameterGroupName: parameterGroup.name,

                // Security and compliance
                deletionProtection: false, // Allow deletion for development
                skipFinalSnapshot: true, // Skip final snapshot for development
                finalSnapshotIdentifier: undefined,

                // Auto minor version updates
                autoMinorVersionUpgrade: true,

                // Tags
                tags: {
                    ...args.tags,
                    Name: `${name}-postgres`,
                    Engine: "postgres",
                    Purpose: "primary-database",
                },
            }, {
                parent: this,
                // Add explicit dependency on subnet group and security group
                dependsOn: [this.subnetGroup, args.databaseSecurityGroup, parameterGroup],
            });
        }

        // Create AWS Secrets Manager secret for database credentials
        this.secret = new aws.secretsmanager.Secret(`${name}-credentials`, {
            name: `${name}-db-credentials-v2`,
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
