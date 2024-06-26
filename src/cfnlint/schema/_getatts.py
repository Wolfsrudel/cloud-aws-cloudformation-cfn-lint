"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

import enum
from collections import UserDict
from typing import Any, Dict, Optional

import regex as re

from cfnlint.schema._pointer import resolve_pointer

_all_property_types = [
    "AWS::Amplify::Branch",
    "AWS::Amplify::Domain",
    "AWS::AppSync::DomainName",
    "AWS::AppSync::FunctionConfiguration",
    "AWS::AppSync::Resolver",
    "AWS::AutoScaling::AutoScalingGroup",
    "AWS::Backup::BackupSelection",
    "AWS::Backup::BackupVault",
    "AWS::CodeArtifact::Domain",
    "AWS::CodeArtifact::Repository",
    "AWS::EC2::CapacityReservation",
    "AWS::EC2::Subnet",
    "AWS::EC2::VPC",
    "AWS::EFS::MountTarget",
    "AWS::EKS::Nodegroup",
    "AWS::ElasticLoadBalancingV2::LoadBalancer",
    "AWS::Events::EventBus",
    "AWS::EventSchemas::Discoverer",
    "AWS::EventSchemas::Registry",
    "AWS::EventSchemas::Schema",
    "AWS::GameLift::GameSessionQueue",
    "AWS::GameLift::MatchmakingConfiguration",
    "AWS::GameLift::MatchmakingRuleSet",
    "AWS::Grafana::Workspace",
    "AWS::ImageBuilder::Component",
    "AWS::ImageBuilder::ContainerRecipe",
    "AWS::ImageBuilder::DistributionConfiguration",
    "AWS::ImageBuilder::ImagePipeline",
    "AWS::ImageBuilder::ImageRecipe",
    "AWS::ImageBuilder::InfrastructureConfiguration",
    "AWS::Neptune::DBCluster",
    "AWS::RDS::DBParameterGroup",
    "AWS::RoboMaker::RobotApplication",
    "AWS::RoboMaker::SimulationApplication",
    "AWS::Route53Resolver::ResolverRule",
    "AWS::Route53Resolver::ResolverRuleAssociation",
    "AWS::S3::AccessPoint",
    "AWS::SageMaker::DataQualityJobDefinition",
    "AWS::SageMaker::ModelBiasJobDefinition",
    "AWS::SageMaker::ModelExplainabilityJobDefinition",
    "AWS::SageMaker::ModelQualityJobDefinition",
    "AWS::SageMaker::MonitoringSchedule",
    "AWS::SNS::Topic",
    "AWS::SQS::Queue",
    "AWS::SSM::Parameter",
    "AWS::StepFunctions::Activity",
]

# Non registry resources that have a difference between readOnlyProperties
# what is supported by GetAtt
_exceptions = {
    "AWS::AppMesh::GatewayRoute": [
        "GatewayRouteName",
        "MeshName",
        "MeshOwner",
        "VirtualGatewayName",
    ],
    "AWS::AppMesh::Mesh": [
        "MeshName",
    ],
    "AWS::AppMesh::Route": [
        "MeshName",
        "MeshOwner",
        "RouteName",
        "VirtualRouterName",
    ],
    "AWS::AppMesh::VirtualGateway": [
        "MeshName",
        "MeshOwner",
        "VirtualGatewayName",
    ],
    "AWS::AppMesh::VirtualNode": [
        "MeshName",
        "MeshOwner",
        "VirtualNodeName",
    ],
    "AWS::AppMesh::VirtualRouter": [
        "MeshName",
        "MeshOwner",
        "VirtualRouterName",
    ],
    "AWS::AppMesh::VirtualService": [
        "MeshName",
        "MeshOwner",
        "VirtualServiceName",
    ],
    "AWS::AppSync::DataSource": [
        "Name",
    ],
    "AWS::Cloud9::EnvironmentEC2": [
        "Name",
    ],
    "AWS::CloudWatch::InsightRule": [
        "RuleName",
    ],
    "AWS::DocDB::DBCluster": [
        "Port",
    ],
    "AWS::EC2::Instance": [
        "AvailabilityZone",
    ],
    "AWS::EC2::SecurityGroup": ["VpcId"],
    "AWS::Greengrass::ConnectorDefinition": [
        "Name",
    ],
    "AWS::Greengrass::CoreDefinition": [
        "Name",
    ],
    "AWS::Greengrass::DeviceDefinition": [
        "Name",
    ],
    "AWS::Greengrass::FunctionDefinition": [
        "Name",
    ],
    "AWS::Greengrass::Group": [
        "Name",
        "RoleArn",
    ],
    "AWS::Greengrass::LoggerDefinition": [
        "Name",
    ],
    "AWS::Greengrass::ResourceDefinition": [
        "Name",
    ],
    "AWS::Greengrass::SubscriptionDefinition": [
        "Name",
    ],
    "AWS::IoT1Click::Device": [
        "Enabled",
    ],
    "AWS::IoT1Click::Placement": [
        "PlacementName",
        "ProjectName",
    ],
    "AWS::IoT1Click::Project": [
        "ProjectName",
    ],
    "AWS::Kinesis::StreamConsumer": [
        "ConsumerName",
        "StreamARN",
    ],
    "AWS::ManagedBlockchain::Member": [
        "NetworkId",
    ],
    "AWS::MediaConvert::JobTemplate": [
        "Name",
    ],
    "AWS::MediaConvert::Preset": [
        "Name",
    ],
    "AWS::MediaConvert::Queue": [
        "Name",
    ],
    "AWS::MediaLive::Input": [
        "Destinations",
        "Sources",
    ],
    "AWS::OpsWorks::Instance": ["AvailabilityZone"],
    "AWS::OpsWorks::UserProfile": ["SshUsername"],
    "AWS::Route53Resolver::ResolverEndpoint": [
        "Direction",
        "Name",
    ],
    "AWS::SageMaker::CodeRepository": ["CodeRepositoryName"],
    "AWS::SageMaker::Endpoint": [
        "EndpointName",
    ],
    "AWS::SageMaker::EndpointConfig": ["EndpointConfigName"],
    "AWS::SageMaker::Model": ["ModelName"],
    "AWS::SageMaker::NotebookInstance": ["NotebookInstanceName"],
    "AWS::SageMaker::NotebookInstanceLifecycleConfig": [
        "NotebookInstanceLifecycleConfigName"
    ],
    "AWS::SageMaker::Workteam": ["WorkteamName"],
    "AWS::ServiceDiscovery::Service": ["Name"],
    "AWS::Transfer::User": [
        "ServerId",
        "UserName",
    ],
}

_unnamed_string_types = ("AWS::CloudFormation::Stack",)

_unnamed_unknown_types = (
    "Custom::",
    "AWS::Serverless::",
    "AWS::CloudFormation::CustomResource",
)


class AttributeDict(UserDict):
    def __init__(self, __dict: None = None) -> None:
        super().__init__(__dict)
        self.data: Dict[str, GetAtt] = {}

    def __getitem__(self, key: str) -> "GetAtt":
        possible_items = {}
        for k, v in self.data.items():
            if re.fullmatch(k, key):
                possible_items[k] = v
        if not possible_items:
            raise KeyError(key)
        longest_match = sorted(possible_items.keys(), key=len)[-1]
        return possible_items[longest_match]

    def __repr__(self) -> str:
        keys = []
        for k in self.data.keys():
            keys.append(k.replace("\\", ""))
        return f"{keys!r}"


class GetAttType(enum.Enum):
    ReadOnly = 1
    All = 2
    Unnamed = 3


class GetAtt:
    def __init__(self, schema: Dict[str, Any], getatt_type: GetAttType) -> None:
        self._getatt_type: GetAttType = getatt_type
        self._type: Optional[str] = schema.get("type")
        self._item_type: Optional[str]
        if self._type == "array":
            self._item_type = schema.get("items", {}).get("type")

    @property
    def type(self) -> Optional[str]:
        return self._type

    @property
    def item_type(self) -> Optional[str]:
        return self._item_type

    @property
    def getatt_type(self) -> GetAttType:
        return self._getatt_type


class GetAtts:
    """Class for helping with GetAtt logic"""

    _attrs: AttributeDict = AttributeDict()
    _schema: Dict[str, Any] = {}

    def __init__(self, schema: Dict[str, Any]) -> None:
        self._attrs = AttributeDict()
        self._schema = schema
        type_name = schema.get("typeName", "")
        if type_name in _all_property_types:
            for name, value in schema.get("properties", {}).items():
                self._process_schema(name, value, GetAttType.All)
            return
        if type_name in _exceptions:
            for name in _exceptions[type_name]:
                attr_schema = self._flatten_schema_by_pointer(f"/properties/{name}")
                self._process_schema(name, attr_schema, GetAttType.ReadOnly)
        for unnamed_type in _unnamed_string_types:
            if type_name.startswith(unnamed_type):
                self._attrs["Outputs\\..*"] = GetAtt(
                    schema={"type": "string"}, getatt_type=GetAttType.Unnamed
                )
        for unnamed_type in _unnamed_unknown_types:
            if type_name.startswith(unnamed_type):
                self._attrs[".*"] = GetAtt(
                    schema={
                        "type": [
                            "string",
                            "number",
                            "boolean",
                            "object",
                            "array",
                            "integer",
                        ]
                    },
                    getatt_type=GetAttType.Unnamed,
                )
        for ro_attr in schema.get("readOnlyProperties", []):
            try:
                name = ".".join(ro_attr.split("/")[2:])
                ro_schema = self._flatten_schema_by_pointer(ro_attr)
                self._process_schema(name, ro_schema, GetAttType.ReadOnly)
            except KeyError:
                pass

    def _flatten_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        r_schema = schema.copy()
        for k, v in schema.items():
            if k == "$ref":
                r_schema.pop(k)
                r_schema = {**r_schema, **self._flatten_schema_by_pointer(v)}
            elif k == "items":
                r_schema[k] = self._flatten_schema(v)
        return r_schema

    def _flatten_schema_by_pointer(self, ptr: str) -> Dict[str, Any]:
        schema = resolve_pointer(self._schema, ptr)
        return self._flatten_schema(schema)

    def _process_schema(
        self, name: str, schema: Dict[str, Any], getatt_type: GetAttType
    ):
        if schema.get("type") == "object":
            for prop, value in schema.get("properties", {}).items():
                self._process_schema(f"{name}.{prop}", value, getatt_type)
        elif schema.get("type") == "array":
            # GetAtt doesn't support going into an array of objects or another array
            # so we only look at an array of strings, etc.
            self._attrs[name] = GetAtt(schema, getatt_type)
        elif schema.get("$ref"):
            schema = resolve_pointer(self._schema, schema.get("$ref"))
            self._process_schema(name, schema, getatt_type)
        else:
            self._attrs[name] = GetAtt(schema, getatt_type)

    @property
    def attrs(self) -> AttributeDict:
        return self._attrs
