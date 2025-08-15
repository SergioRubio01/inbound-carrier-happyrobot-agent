import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

export interface NetworkingArgs {
    cidrBlock: string;
    availabilityZones: number;
    environment: string;
    tags: Record<string, string>;
}

export class NetworkingComponent extends pulumi.ComponentResource {
    public readonly vpc: aws.ec2.Vpc;
    public readonly internetGateway: aws.ec2.InternetGateway;
    public readonly publicSubnets: aws.ec2.Subnet[];
    public readonly privateSubnets: aws.ec2.Subnet[];
    public readonly natGateways: aws.ec2.NatGateway[];
    public readonly publicRouteTable: aws.ec2.RouteTable;
    public readonly privateRouteTables: aws.ec2.RouteTable[];
    public readonly albSecurityGroup: aws.ec2.SecurityGroup;
    public readonly ecsSecurityGroup: aws.ec2.SecurityGroup;
    public readonly databaseSecurityGroup: aws.ec2.SecurityGroup;

    constructor(name: string, args: NetworkingArgs, opts?: pulumi.ComponentResourceOptions) {
        super("happyrobot:networking", name, {}, opts);

        // Get available AZs
        const availabilityZones = aws.getAvailabilityZones({
            state: "available",
        });

        // Create VPC
        this.vpc = new aws.ec2.Vpc(`${name}-vpc`, {
            cidrBlock: args.cidrBlock,
            enableDnsHostnames: true,
            enableDnsSupport: true,
            tags: {
                ...args.tags,
                Name: `${name}-vpc`,
            },
        }, { parent: this });

        // Create Internet Gateway
        this.internetGateway = new aws.ec2.InternetGateway(`${name}-igw`, {
            vpcId: this.vpc.id,
            tags: {
                ...args.tags,
                Name: `${name}-igw`,
            },
        }, { parent: this });

        // Create public subnets
        this.publicSubnets = [];
        for (let i = 0; i < args.availabilityZones; i++) {
            const subnet = new aws.ec2.Subnet(`${name}-public-subnet-${i + 1}`, {
                vpcId: this.vpc.id,
                cidrBlock: `10.0.${100 + i}.0/24`,
                availabilityZone: availabilityZones.then(azs => azs.names[i % azs.names.length]),
                mapPublicIpOnLaunch: true,
                tags: {
                    ...args.tags,
                    Name: `${name}-public-subnet-${i + 1}`,
                    Type: "public",
                },
            }, { parent: this });
            this.publicSubnets.push(subnet);
        }

        // Create private subnets
        this.privateSubnets = [];
        for (let i = 0; i < args.availabilityZones; i++) {
            const subnet = new aws.ec2.Subnet(`${name}-private-subnet-${i + 1}`, {
                vpcId: this.vpc.id,
                cidrBlock: `10.0.${i + 1}.0/24`,
                availabilityZone: availabilityZones.then(azs => azs.names[i % azs.names.length]),
                mapPublicIpOnLaunch: false,
                tags: {
                    ...args.tags,
                    Name: `${name}-private-subnet-${i + 1}`,
                    Type: "private",
                },
            }, { parent: this });
            this.privateSubnets.push(subnet);
        }

        // Create Elastic IPs for NAT Gateways
        const elasticIps = [];
        for (let i = 0; i < args.availabilityZones; i++) {
            const eip = new aws.ec2.Eip(`${name}-nat-eip-${i + 1}`, {
                domain: "vpc",
                tags: {
                    ...args.tags,
                    Name: `${name}-nat-eip-${i + 1}`,
                },
            }, { parent: this });
            elasticIps.push(eip);
        }

        // Create NAT Gateways
        this.natGateways = [];
        for (let i = 0; i < args.availabilityZones; i++) {
            const natGw = new aws.ec2.NatGateway(`${name}-nat-gateway-${i + 1}`, {
                subnetId: this.publicSubnets[i].id,
                allocationId: elasticIps[i].id,
                tags: {
                    ...args.tags,
                    Name: `${name}-nat-gateway-${i + 1}`,
                },
            }, { parent: this });
            this.natGateways.push(natGw);
        }

        // Create public route table
        this.publicRouteTable = new aws.ec2.RouteTable(`${name}-public-rt`, {
            vpcId: this.vpc.id,
            routes: [
                {
                    cidrBlock: "0.0.0.0/0",
                    gatewayId: this.internetGateway.id,
                },
            ],
            tags: {
                ...args.tags,
                Name: `${name}-public-rt`,
            },
        }, { parent: this });

        // Associate public subnets with public route table
        for (let i = 0; i < this.publicSubnets.length; i++) {
            new aws.ec2.RouteTableAssociation(`${name}-public-rta-${i + 1}`, {
                subnetId: this.publicSubnets[i].id,
                routeTableId: this.publicRouteTable.id,
            }, { parent: this });
        }

        // Create private route tables (one per AZ)
        this.privateRouteTables = [];
        for (let i = 0; i < args.availabilityZones; i++) {
            const privateRt = new aws.ec2.RouteTable(`${name}-private-rt-${i + 1}`, {
                vpcId: this.vpc.id,
                routes: [
                    {
                        cidrBlock: "0.0.0.0/0",
                        natGatewayId: this.natGateways[i].id,
                    },
                ],
                tags: {
                    ...args.tags,
                    Name: `${name}-private-rt-${i + 1}`,
                },
            }, { parent: this });
            this.privateRouteTables.push(privateRt);

            // Associate private subnet with private route table
            new aws.ec2.RouteTableAssociation(`${name}-private-rta-${i + 1}`, {
                subnetId: this.privateSubnets[i].id,
                routeTableId: privateRt.id,
            }, { parent: this });
        }

        // Create security groups

        // ALB Security Group - Allow HTTP/HTTPS from internet
        this.albSecurityGroup = new aws.ec2.SecurityGroup(`${name}-alb-sg`, {
            name: `${name}-alb-sg`,
            description: "Security group for Application Load Balancer",
            vpcId: this.vpc.id,
            ingress: [
                {
                    description: "HTTP",
                    fromPort: 80,
                    toPort: 80,
                    protocol: "tcp",
                    cidrBlocks: ["0.0.0.0/0"],
                },
                {
                    description: "HTTPS",
                    fromPort: 443,
                    toPort: 443,
                    protocol: "tcp",
                    cidrBlocks: ["0.0.0.0/0"],
                },
            ],
            egress: [
                {
                    description: "All outbound traffic",
                    fromPort: 0,
                    toPort: 0,
                    protocol: "-1",
                    cidrBlocks: ["0.0.0.0/0"],
                },
            ],
            tags: {
                ...args.tags,
                Name: `${name}-alb-sg`,
            },
        }, { parent: this });

        // ECS Security Group - Allow traffic from ALB and to database
        this.ecsSecurityGroup = new aws.ec2.SecurityGroup(`${name}-ecs-sg`, {
            name: `${name}-ecs-sg`,
            description: "Security group for ECS Fargate tasks",
            vpcId: this.vpc.id,
            ingress: [
                {
                    description: "From ALB to API",
                    fromPort: 8000,
                    toPort: 8000,
                    protocol: "tcp",
                    securityGroups: [this.albSecurityGroup.id],
                },
                {
                    description: "From ALB to Web",
                    fromPort: 3000,
                    toPort: 3000,
                    protocol: "tcp",
                    securityGroups: [this.albSecurityGroup.id],
                },
            ],
            egress: [
                {
                    description: "All outbound traffic",
                    fromPort: 0,
                    toPort: 0,
                    protocol: "-1",
                    cidrBlocks: ["0.0.0.0/0"],
                },
            ],
            tags: {
                ...args.tags,
                Name: `${name}-ecs-sg`,
            },
        }, { parent: this });

        // Database Security Group - Allow traffic from ECS only
        this.databaseSecurityGroup = new aws.ec2.SecurityGroup(`${name}-db-sg`, {
            name: `${name}-db-sg`,
            description: "Security group for RDS PostgreSQL database",
            vpcId: this.vpc.id,
            ingress: [
                {
                    description: "PostgreSQL from ECS",
                    fromPort: 5432,
                    toPort: 5432,
                    protocol: "tcp",
                    securityGroups: [this.ecsSecurityGroup.id],
                },
            ],
            egress: [
                {
                    description: "All outbound traffic",
                    fromPort: 0,
                    toPort: 0,
                    protocol: "-1",
                    cidrBlocks: ["0.0.0.0/0"],
                },
            ],
            tags: {
                ...args.tags,
                Name: `${name}-db-sg`,
            },
        }, { parent: this });

        // Register outputs
        this.registerOutputs({
            vpc: this.vpc,
            internetGateway: this.internetGateway,
            publicSubnets: this.publicSubnets,
            privateSubnets: this.privateSubnets,
            natGateways: this.natGateways,
            publicRouteTable: this.publicRouteTable,
            privateRouteTables: this.privateRouteTables,
            albSecurityGroup: this.albSecurityGroup,
            ecsSecurityGroup: this.ecsSecurityGroup,
            databaseSecurityGroup: this.databaseSecurityGroup,
        });
    }
}
