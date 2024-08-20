###
# Copyright (c) 2023 Solareon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
###

import re
import requests
from yahooquery import Ticker
from datetime import datetime, timedelta

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Stocks')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class Stocks(callbacks.Plugin):
    """Provides access to stocks data"""
    threaded = True

    def get_forex(self, irc, session, symbol1, symbol2):
        api_key = self.registryValue('alphavantage.api.key')
        if not api_key:
            irc.error('Missing API key, ask the admin to get one and set '
                      'supybot.plugins.Stocks.alphavantage.api.key', Raise=True)
        try:
            return session.get('https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={symbol1}&to_currency={symbol2}&apikey={api_key}'.format(symbol1=symbol1,symbol2=symbol2,
                api_key=api_key)).json()
        except Exception:
            raise


    def get_stocks(self, irc, symbol):
        # Do regex checking on symbol to ensure it's valid
        if not re.match(r'^[\w^=:.\-]{1,10}$', symbol):
            irc.errorInvalid('symbol', symbol, Raise=True)

        # Get data from API
        ticker = Ticker(symbol)

        if not ticker.price:
            irc.error("{symbol}: An error occurred.".format(symbol=symbol), Raise=True)

        if 'error' in ticker.price.keys():
            irc.error("{symbol}: {message}".format(symbol=symbol, message=ticker.price['error']['description']), Raise=True)
            
        print("Ticker price data:", ticker.price)

        market_state = ticker.price.get('marketState')  # Access 'marketState' from the dictionary
        quote_type = ticker.price.get('quoteType')  # Access 'quoteType' from the dictionary

        if quote_type == 'INDEX' or market_state == 'REGULAR':
            price = ticker.price.get('regularMarketPrice')
            market_state = 'Open'
        elif market_state == 'POST':
            price = ticker.price.get('postMarketPrice')
            market_state = 'Post-market'
        elif market_state == 'PRE':
            price = ticker.price.get('preMarketPrice')
            market_state = 'Pre-market'
        else:
            price = ticker.price.get('regularMarketPrice')

        short_name = ticker.price.get('shortName')
        close = ticker.price.get('regularMarketPreviousClose')
        currency = ticker.price.get('currencySymbol')
        day_high = ticker.price.get('regularMarketDayHigh')
        day_low = ticker.price.get('regularMarketDayLow')
        change = round(price - close,2)
        change_percent = round(change / close * 100, 2)

        message = (
            '{symbol} : {short_name} {currency}{price:g} '
        )

        if change >= 0.0:
            message += ircutils.mircColor('\u25b2 {change:g} ({change_percent:g}%)', 'green')
        else:
            message += ircutils.mircColor('\u25bc {change:g} ({change_percent:g}%)', 'red')

        message += " High: {day_high} Low: {day_low}"
        if quote_type != 'INDEX':
            message += " {market_state}"

        message = message.format(
            symbol=ircutils.bold(symbol),
            short_name=short_name,
            currency=currency,
            price=price,
            change=change,
            change_percent=change_percent,
            day_high=day_high,
            day_low=day_low,
            market_state=market_state,
        )

        return message
    
    def get_forexs(self, irc, session, forex1, forex2):
        # Do regex checking on symbol to ensure it's valid
        if not re.match(r'^[\w^=:.\-]{1,3}$', forex1):
            irc.errorInvalid('forex', forex1, Raise=True)

        if not re.match(r'^[\w^=:.\-]{1,3}$', forex2):
            irc.errorInvalid('forex', forex2, Raise=True)

        # Get data from API
        data = self.get_forex(irc, session, forex1, forex2)

        if not data:
            irc.error("{forex1},{forex2}: An error occurred.".format(forex1=forex1,forex2=forex2), Raise=True)

        if 'Error Message' in data.keys():
            irc.error("{forex1},{forex2}: {message}".format(forex1=forex1,forex2=forex2, message=data['Error Message']), Raise=True)

        forex1_symbol = data['Realtime Currency Exchange Rate']['1. From_Currency Code']
        forex1 = data['Realtime Currency Exchange Rate']['2. From_Currency Name']
        forex2_symbol = data['Realtime Currency Exchange Rate']['3. To_Currency Code']
        forex2 = data['Realtime Currency Exchange Rate']['4. To_Currency Name']
        price = float(data['Realtime Currency Exchange Rate']['5. Exchange Rate'])

        message = (
            '{forex1_symbol}:{forex1} to {forex2_symbol}:{forex2} {price:g}'
        )

        message = message.format(
            forex1_symbol=ircutils.bold(forex1_symbol),
            forex1=forex1,
            forex2_symbol=ircutils.bold(forex2_symbol),
            forex2=forex2,
            price=price,
        )

        return message

    @wrap([many('something')])
    def stock(self, irc, msg, args, symbols):
        """<symbol> [<symbol> [<symbol> ...]]

        Returns stock data for single or multiple symbols"""

        max_symbols = self.registryValue('maxsymbols')
        count_symbols = len(symbols)

        if count_symbols > max_symbols:
            irc.error("Too many symbols. Maximum count {}. Your count: {}".format(max_symbols, count_symbols), Raise=True)

        messages = map(lambda symbol: self.get_stocks(irc, symbol), symbols)

        irc.replies(messages, joiner=' | ')

    @wrap([many('something')])
    def crypto(self, irc, msg, args, cryptos):
        """<crypto> [<crypto> [<crypto> ...]]

        Returns cryptocurrency data for single or multiple symbols to a configured fiat pair"""

        max_symbols = self.registryValue('maxsymbols')
        count_symbols = len(cryptos)
        fiat = '-'+self.registryValue('cryptofiat')

        if count_symbols > max_symbols:
            irc.error("Too many symbols. Maximum count {}. Your count: {}".format(max_symbols, count_symbols), Raise=True)

        messages = map(lambda symbol: self.get_stocks(irc, symbol+fiat), cryptos)

        irc.replies(messages, joiner=' | ')

    @wrap(["somethingWithoutSpaces", "somethingWithoutSpaces"])
    def forex(self, irc, msg, args, symbol1, symbol2):
        """<symbol> <symbol>

        Returns forex data for single symbol pair"""

        with requests.Session() as session:
            message = self.get_forexs(irc, session, symbol1, symbol2)

        irc.reply(message)

    def sindex(self, irc, msg, args):
        """takes no arguments

        Returns indexes for us markets"""

        symbols = ['^DJI', '^GSPC', '^IXIC', '^RUT']
        messages = map(lambda symbol: self.get_stocks(irc, symbol), symbols)

        irc.replies(messages, joiner=' | ')

    sindex = wrap(sindex)

    def findex(self, irc, msg, args):
        """takes no arguments

        Returns indexes for world markets"""

        symbols = ['^GDAXI', '^FCHI', '^FTSE', '^N225']
        messages = map(lambda symbol: self.get_stocks(irc, symbol), symbols)

        irc.replies(messages, joiner=' | ')

    findex = wrap(findex)

Class = Stocks


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
