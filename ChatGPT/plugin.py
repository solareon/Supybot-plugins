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
import privatebinapi
import requests
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

    def send_reply(self, irc, message):
        if len(message) > 400:
            split_index = message[:400].rfind(".")
            if split_index == -1: # If no space or dot found before the 400th character
                split_index = 399 # Split at the 399th character
            irc.reply(message[:split_index])
            remaining_message = message[split_index:]
            while len(remaining_message) > 400:
                split_index = message[:400].rfind(".")
                if split_index == -1:
                    split_index = 399
                irc.reply(remaining_message[:split_index], prefixNick=False)
                remaining_message = remaining_message[split_index:]
            irc.reply(remaining_message, prefixNick=False)
        else:
            irc.reply(message)

    def get_paste(self, irc, message):
        shorten = self.registryValue('shorten.enable')
        shorten_url = self.registryValue('shorten.url')+"/api/v2/links"
        shorten_api = self.registryValue('shorten.api.key')
        pb_url = self.registryValue('privatebin.url')

        if not pb_url:
            irc.error('Missing Privatebin URL, ask the admin to get one and set '
                      'supybot.plugins.ChatGPT.privatebin.url', Raise=True)

        if shorten and not shorten_url:
            irc.error('Missing Kutt URL, ask the admin to get one and set '
                      'supybot.plugins.ChatGPT.shorten.url', Raise=True)
            
        try:
            send_response = privatebinapi.send(pb_url, text=message)
            get_response = privatebinapi.get(send_response["full_url"])
            
            if shorten:
                payload = {"target": get_response}
                headers = {'X-API-KEY': shorten_api,'Content-Type': 'application/json'}
                response = requests.post(shorten_url, headers=headers, json=payload).json()
                short = response['link']
                return short
            
            return get_response
        except Exception:
            raise


    def chatgpt(self, irc, msg, args, message):
        """<prompt>

        Returns ChatGPT response to prompt"""
        model = "gpt-3.5-turbo"

        completion = self.get_chatgpt(irc, model, message)
        messages = ""
        for choice in completion.choices:
            messages += choice.message.content.strip()
        messages = messages.replace('\n', ' ')

        self.send_reply(irc, messages)

    chatgpt = wrap(chatgpt, ['text'])

    def gpt3(self, irc, msg, args, message):
        """<prompt>

        Returns text-davinci-003 response to prompt"""
        model = "text-davinci-003"

        completion = self.get_completion(irc, model, message)
        messages = ""
        for choice in completion.choices:
            messages += choice.text.strip()
        messages = messages.replace('\n', ' ')

        self.send_reply(irc, messages)

    gpt3 = wrap(gpt3, ['text'])

    def codex(self, irc, msg, args, message):
        """<prompt>

        Returns Codex response to prompt"""
        model = "code-davinci-002"

        completion = self.get_completion(irc, model, message)
        messages = ""
        for choice in completion.choices:
            messages += choice.text.strip()
        #messages = messages.replace('\n', ' ')

        paste = self.get_paste(irc, messages)
        irc.reply(paste)

    codex = wrap(codex, ['text'])
    

Class = ChatGPT


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
