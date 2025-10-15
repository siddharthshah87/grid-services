"""
Tests to ensure VEN MQTT stability and prevent regression of connection issues.

These tests verify:
1. No duplicate subscriptions
2. No duplicate loop_start() calls
3. Proper initialization order
4. Connection state management
5. Backend command topic subscription
"""

import re
from pathlib import Path


def test_no_duplicate_subscriptions_in_main():
    """Ensure main() function does not contain duplicate MQTT subscriptions."""
    ven_agent_path = Path(__file__).parent.parent / "ven_agent.py"
    content = ven_agent_path.read_text()
    
    # Find main() function
    main_match = re.search(r'def main\(.*?\):(.*?)(?=\ndef |\nif __name__|$)', content, re.DOTALL)
    assert main_match, "Could not find main() function"
    
    main_body = main_match.group(1)
    
    # Check that main() does NOT contain subscribe calls
    subscribe_calls = re.findall(r'client\.subscribe\(', main_body)
    assert len(subscribe_calls) == 0, (
        f"Found {len(subscribe_calls)} client.subscribe() calls in main() function. "
        "Subscriptions should only happen in _subscribe_topics()"
    )
    
    # Check that main() does NOT contain message_callback_add calls
    callback_calls = re.findall(r'client\.message_callback_add\(', main_body)
    assert len(callback_calls) == 0, (
        f"Found {len(callback_calls)} client.message_callback_add() calls in main() function. "
        "Message callbacks should only be added in _subscribe_topics()"
    )


def test_backend_cmd_topic_subscription():
    """Ensure BACKEND_CMD_TOPIC is subscribed in _subscribe_topics()."""
    ven_agent_path = Path(__file__).parent.parent / "ven_agent.py"
    content = ven_agent_path.read_text()
    
    # Find _subscribe_topics() function - use more specific pattern
    subscribe_match = re.search(
        r'def _subscribe_topics\(\) -> None:(.*?)(?=\n\ndef )', 
        content, 
        re.DOTALL
    )
    assert subscribe_match, "Could not find _subscribe_topics() function"
    
    subscribe_body = subscribe_match.group(1)
    
    # Check that BACKEND_CMD_TOPIC is subscribed
    assert 'BACKEND_CMD_TOPIC' in subscribe_body, (
        "BACKEND_CMD_TOPIC not found in _subscribe_topics(). "
        "Backend commands will not be received!"
    )
    
    # Check that backend callback is added
    assert 'on_backend_cmd' in subscribe_body, (
        "on_backend_cmd callback not added in _subscribe_topics()"
    )


def test_single_loop_start_call():
    """Ensure client.loop_start() is only called once (in _ven_enable)."""
    ven_agent_path = Path(__file__).parent.parent / "ven_agent.py"
    content = ven_agent_path.read_text()
    
    # Find all loop_start() calls (excluding comments)
    lines = content.split('\n')
    loop_start_lines = [
        i for i, line in enumerate(lines, 1)
        if 'client.loop_start()' in line and not line.strip().startswith('#')
    ]
    
    # Should only be called in _ven_enable() function
    assert len(loop_start_lines) == 1, (
        f"Found {len(loop_start_lines)} client.loop_start() calls at lines {loop_start_lines}. "
        "Should only be called once in _ven_enable() function"
    )
    
    # Verify it's in _ven_enable()
    ven_enable_match = re.search(r'def _ven_enable\(.*?\):(.*?)(?=\ndef )', content, re.DOTALL)
    assert ven_enable_match, "Could not find _ven_enable() function"
    
    ven_enable_body = ven_enable_match.group(1)
    assert 'client.loop_start()' in ven_enable_body, (
        "client.loop_start() not found in _ven_enable() function"
    )


def test_mqtt_initialization_after_handlers():
    """Ensure MQTT initialization happens after all handlers are defined."""
    ven_agent_path = Path(__file__).parent.parent / "ven_agent.py"
    content = ven_agent_path.read_text()
    lines = content.split('\n')
    
    # Find line numbers for key elements
    on_event_line = None
    on_backend_cmd_line = None
    ven_enable_call_line = None
    
    for i, line in enumerate(lines, 1):
        if 'def on_event(' in line:
            on_event_line = i
        if 'def on_backend_cmd(' in line:
            on_backend_cmd_line = i
        if '_ven_enable()' in line and 'def _ven_enable' not in line and not line.strip().startswith('#'):
            # This is a call to _ven_enable(), not the definition
            ven_enable_call_line = i
    
    assert on_event_line, "Could not find on_event() function definition"
    assert on_backend_cmd_line, "Could not find on_backend_cmd() function definition"
    assert ven_enable_call_line, "Could not find _ven_enable() call at module level"
    
    # Verify initialization happens AFTER all handlers
    assert ven_enable_call_line > on_event_line, (
        f"_ven_enable() called at line {ven_enable_call_line} before on_event() defined at line {on_event_line}. "
        "This will cause NameError!"
    )
    assert ven_enable_call_line > on_backend_cmd_line, (
        f"_ven_enable() called at line {ven_enable_call_line} before on_backend_cmd() defined at line {on_backend_cmd_line}. "
        "This will cause NameError!"
    )


def test_shadow_publish_has_connection_checks():
    """Ensure shadow publish functions check connection status before publishing."""
    ven_agent_path = Path(__file__).parent.parent / "ven_agent.py"
    content = ven_agent_path.read_text()
    
    # Find _shadow_merge_report() function
    shadow_merge_match = re.search(
        r'def _shadow_merge_report\(.*?\):(.*?)(?=\ndef )', 
        content, 
        re.DOTALL
    )
    assert shadow_merge_match, "Could not find _shadow_merge_report() function"
    
    shadow_merge_body = shadow_merge_match.group(1)
    
    # Check for connection check before publishing
    assert 'if not connected' in shadow_merge_body or 'connected' in shadow_merge_body, (
        "_shadow_merge_report() does not check connection status before publishing. "
        "This can cause publish-while-disconnected errors!"
    )


def test_no_shadow_updates_in_callbacks():
    """Ensure _on_connect and _on_disconnect do not call shadow update functions."""
    ven_agent_path = Path(__file__).parent.parent / "ven_agent.py"
    content = ven_agent_path.read_text()
    
    # Find _on_connect() function
    on_connect_match = re.search(r'def _on_connect\(.*?\):(.*?)(?=\ndef )', content, re.DOTALL)
    assert on_connect_match, "Could not find _on_connect() function"
    on_connect_body = on_connect_match.group(1)
    
    # Find _on_disconnect() function
    on_disconnect_match = re.search(r'def _on_disconnect\(.*?\):(.*?)(?=\ndef )', content, re.DOTALL)
    assert on_disconnect_match, "Could not find _on_disconnect() function"
    on_disconnect_body = on_disconnect_match.group(1)
    
    # Check that callbacks don't call shadow update functions
    shadow_funcs = ['_shadow_merge_report', '_shadow_publish_desired']
    
    for func in shadow_funcs:
        assert func not in on_connect_body, (
            f"_on_connect() calls {func}(). "
            "Shadow updates in connection callbacks can cause reconnect storms!"
        )
        assert func not in on_disconnect_body, (
            f"_on_disconnect() calls {func}(). "
            "Shadow updates in disconnect callbacks can cause reconnect storms!"
        )


def test_ven_enable_checks_connection():
    """Ensure _ven_enable() checks connection status before calling connect()."""
    ven_agent_path = Path(__file__).parent.parent / "ven_agent.py"
    content = ven_agent_path.read_text()
    
    # Find _ven_enable() function
    ven_enable_match = re.search(r'def _ven_enable\(.*?\):(.*?)(?=\ndef )', content, re.DOTALL)
    assert ven_enable_match, "Could not find _ven_enable() function"
    
    ven_enable_body = ven_enable_match.group(1)
    
    # Check that it has logic to avoid duplicate connections
    # Either checks is_connected() or has early return based on connection state
    has_connection_check = (
        'is_connected()' in ven_enable_body or 
        'and connected' in ven_enable_body or
        'connected' in ven_enable_body
    )
    
    assert has_connection_check, (
        "_ven_enable() does not check connection status. "
        "This can cause duplicate connection attempts!"
    )


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
