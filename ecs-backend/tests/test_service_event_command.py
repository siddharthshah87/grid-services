"""Tests for event command service."""
import pytest
import asyncio
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.services.event_command_service import EventCommandService, EventCommandServiceError
from app.core.config import Settings


@pytest.fixture
async def test_engine():
    """Create in-memory test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = Mock(spec=Settings)
    config.event_command_enabled = True
    config.iot_endpoint = "test-endpoint.iot.us-west-2.amazonaws.com"
    config.event_monitor_interval_s = 1
    return config


@pytest.fixture
async def session_factory(test_session):
    """Create session factory for service."""
    async def _factory():
        yield test_session
    return _factory


@pytest.mark.asyncio
async def test_service_init(mock_config, session_factory):
    """Test service initialization."""
    service = EventCommandService(config=mock_config, session_factory=session_factory)
    assert service._config == mock_config
    assert service._started is False
    assert service._iot_client is None


@pytest.mark.asyncio
async def test_service_disabled_by_config():
    """Test service doesn't start when disabled in config."""
    config = Mock(spec=Settings)
    config.event_command_enabled = False
    
    service = EventCommandService(config=config)
    await service.start()
    
    assert service._started is False
    assert service._iot_client is None


@pytest.mark.asyncio
async def test_service_no_iot_endpoint():
    """Test service doesn't start without IoT endpoint."""
    config = Mock(spec=Settings)
    config.event_command_enabled = True
    config.iot_endpoint = None
    
    service = EventCommandService(config=config)
    await service.start()
    
    assert service._started is False


@pytest.mark.asyncio
@patch('boto3.client')
async def test_service_start_success(mock_boto_client, mock_config, session_factory):
    """Test successful service startup."""
    mock_iot_client = MagicMock()
    mock_boto_client.return_value = mock_iot_client
    
    service = EventCommandService(config=mock_config, session_factory=session_factory)
    
    try:
        await service.start()
        
        # Verify boto3 client was created
        mock_boto_client.assert_called_once()
        call_kwargs = mock_boto_client.call_args[1]
        assert call_kwargs['region_name'] in ['us-west-2', 'AWS_REGION']
        assert 'endpoint_url' in call_kwargs
        
        # Give the monitor task a moment to start
        await asyncio.sleep(0.1)
        
        assert service._iot_client == mock_iot_client
        assert service._started is True
    finally:
        await service.stop()


@pytest.mark.asyncio
@patch('boto3.client')
async def test_service_start_idempotent(mock_boto_client, mock_config, session_factory):
    """Test calling start multiple times is safe."""
    mock_boto_client.return_value = MagicMock()
    
    service = EventCommandService(config=mock_config, session_factory=session_factory)
    
    try:
        await service.start()
        await service.start()  # Second call should be no-op
        
        # Should only create client once
        assert mock_boto_client.call_count == 1
    finally:
        await service.stop()


@pytest.mark.asyncio
@patch('boto3.client')
async def test_service_stop(mock_boto_client, mock_config, session_factory):
    """Test stopping the service."""
    mock_boto_client.return_value = MagicMock()
    
    service = EventCommandService(config=mock_config, session_factory=session_factory)
    
    await service.start()
    await asyncio.sleep(0.1)  # Let monitor task start
    
    await service.stop()
    
    assert service._started is False
    if service._monitor_task:
        assert service._monitor_task.cancelled() or service._monitor_task.done()


@pytest.mark.asyncio
async def test_service_stop_when_not_started(mock_config, session_factory):
    """Test stopping when service was never started."""
    service = EventCommandService(config=mock_config, session_factory=session_factory)
    
    # Should not raise
    await service.stop()
    assert service._started is False


@pytest.mark.asyncio
@patch('boto3.client')
async def test_service_tracks_dispatched_events(mock_boto_client, mock_config, session_factory):
    """Test that service tracks which events have been dispatched."""
    mock_boto_client.return_value = MagicMock()
    
    service = EventCommandService(config=mock_config, session_factory=session_factory)
    
    assert len(service._dispatched_events) == 0
    assert len(service._completed_events) == 0


@pytest.mark.asyncio
@patch('boto3.client', side_effect=Exception("AWS error"))
async def test_service_start_boto_error(mock_boto_client, mock_config, session_factory):
    """Test service handles boto3 client creation errors."""
    service = EventCommandService(config=mock_config, session_factory=session_factory)
    
    with pytest.raises(EventCommandServiceError) as exc_info:
        await service.start()
    
    assert "Failed to initialize IoT client" in str(exc_info.value)


@pytest.mark.asyncio
@patch('boto3.client')
async def test_service_monitor_task_created(mock_boto_client, mock_config, session_factory):
    """Test that monitor task is created on start."""
    mock_boto_client.return_value = MagicMock()
    
    service = EventCommandService(config=mock_config, session_factory=session_factory)
    
    try:
        await service.start()
        await asyncio.sleep(0.1)  # Let task start
        
        assert service._monitor_task is not None
        assert isinstance(service._monitor_task, asyncio.Task)
        assert not service._monitor_task.done()
    finally:
        await service.stop()
