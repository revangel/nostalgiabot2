"""
Test module for NostalgiaBot
"""

pytest_plugins = ["errbot.backends.test"]

extra_plugin_dir = '.'

def test_remember(testbot):
    user = "@TestUser"
    quote = "This is some message."
    command = '!remember that {} said {}'.format(user, quote)

    plugin = testbot._bot.plugin_manager.get_plugin_obj_by_name('NostalgiaBot')

    testbot.push_message(command)

    assert "Memory stored!" in testbot.pop_message()
    assert user in plugin
    assert quote in plugin[user]

def test_remind(testbot):
    pass

def test_converse(testbot):
    pass