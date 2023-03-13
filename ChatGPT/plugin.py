###
# Copyright (c) 2023, Solareon
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import re
import openai
from datetime import datetime, timedelta

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('ChatGPT')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class ChatGPT(callbacks.Plugin):
    """A plugin to provide responses via ChatGPT's API"""
    threaded = True

    def get_completion(self, irc, model, message):
        openai.api_key = self.registryValue('openai.api.key')
        max_tokens = self.registryValue('openai.maxtokens')
        if not openai.api_key:
            irc.error('Missing API key, ask the admin to get one and set '
                      'supybot.plugins.ChatGPT.openai.api.key', Raise=True)
        
        try:
            completion = openai.Completion.create(model=model,prompt=message,max_tokens=max_tokens)
            return completion
        except Exception:
            raise

    def get_chatgpt(self, irc, model, message):
        openai.api_key = self.registryValue('openai.api.key')
        max_tokens = self.registryValue('openai.maxtokens')
        if not openai.api_key:
            irc.error('Missing API key, ask the admin to get one and set '
                      'supybot.plugins.ChatGPT.openai.api.key', Raise=True)
        
        try:
            completion = openai.ChatCompletion.create(model=model,messages=[{"role": "user", "content": message}])
            return completion
        except Exception:
            raise

    def chatgpt(self, irc, msg, args, message):
        """<prompt>

        Returns ChatGPT response to prompt"""
        model = "gpt-3.5-turbo"

        messages = self.get_chatgpt(irc, model, message)
        for choice in messages.choices:
            irc.reply(choice.message.content.strip(), prefixNick=False, noLengthCheck=True)

    chatgpt = wrap(chatgpt, ['text'])

    def gpt3(self, irc, msg, args, message):
        """<prompt>

        Returns ChatGPT response to prompt"""
        model = "text-davinci-003"

        messages = self.get_completion(irc, model, message)
        for choice in messages.choices:
            irc.reply(choice.text.strip(), prefixNick=False, noLengthCheck=True)

    gpt3 = wrap(chatgpt, ['text'])

    

Class = ChatGPT


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
