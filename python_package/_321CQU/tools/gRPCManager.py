from contextlib import asynccontextmanager
from enum import Enum
from typing import Tuple

from grpc.aio import insecure_channel
from micro_services_protobuf.notification_center import apns_pb2_grpc as apns_grpc
from micro_services_protobuf.mycqu_service import mycqu_service_pb2_grpc as mycqu_grpc
from micro_services_protobuf.edu_admin_center import eac_service_pb2_grpc as eac_grpc

from .._mock import MockApnStub
from .ConfigHandler import _CONFIG_HANDLER, ConfigHandler
from .Singleton import Singleton

__all__ = ['gRPCManager', 'ServiceEnum', 'MockGRPCManager']


class ServiceEnum(str, Enum):
    NotificationCenter = 'notification_center'
    MycquService = 'mycqu_service'
    CardService = 'mycqu_service'
    EduAdminCenter = 'edu_admin_center'

    def _get_stub_class(self):
        if self == ServiceEnum.NotificationCenter:
            return apns_grpc.ApnsStub
        elif self == ServiceEnum.MycquService:
            return mycqu_grpc.MycquFetcherStub
        elif self == ServiceEnum.CardService:
            return mycqu_grpc.CardFetcherStub
        elif self == ServiceEnum.EduAdminCenter:
            return eac_grpc.EduAdminCenterStub
        else:
            raise RuntimeError("未提供对应服务Stub")

    def _get_mock_stub_class(self):
        if self == ServiceEnum.NotificationCenter:
            return MockApnStub
        else:
            raise RuntimeError("未提供对应Mock")


class gRPCManager(metaclass=Singleton):
    def __init__(self, handler: ConfigHandler = _CONFIG_HANDLER):
        all_options = handler.get_options('ServiceSetting')

        service_hosts = list(filter(lambda x: x.endswith('_service_host'), all_options))
        service_ports = list(filter(lambda x: x.endswith('_service_port'), all_options))
        self._service_host = {}
        self._service_ports = {}

        for host in service_hosts:
            self._service_host.update({
                host: handler.get_config("ServiceSetting", host)
            })

        for port in service_ports:
            self._service_ports.update({
                port: handler.get_config("ServiceSetting", port)
            })

    def get_service_config(self, service: ServiceEnum) -> Tuple[str, str]:
        return (self._service_host[service.value + "_service_host"],
                self._service_ports[service.value + "_service_port"])

    @asynccontextmanager
    async def get_stub(self, service: ServiceEnum):
        target = service._get_stub_class()

        if target is not None:
            host = self._service_host[service.value + "_service_host"]
            port = self._service_ports[service.value + "_service_port"]
            target_url = host + ":" + port
            async with insecure_channel(target_url) as channel:
                yield target(channel)


class MockGRPCManager(gRPCManager):
    @asynccontextmanager
    async def get_stub(self, service: ServiceEnum):
        yield service._get_mock_stub_class()()
