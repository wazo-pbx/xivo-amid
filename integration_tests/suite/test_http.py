# -*- coding: utf-8 -*-
# Copyright (C) 2015 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from .base import BaseIntegrationTest
from .base import VALID_TOKEN

from hamcrest import assert_that
from hamcrest import contains
from hamcrest import equal_to
from hamcrest import has_entries
from hamcrest import matches_regexp


class TestHTTP(BaseIntegrationTest):

    asset = 'http_only'

    def test_that_action_ping_returns_pong(self):
        result = self.action('Ping')

        assert_that(result, contains(has_entries({
            'Response': 'Success',
            'Ping': 'Pong',
            'Timestamp': matches_regexp('.*')
        })))

    def test_that_action_queues_is_refused(self):
        result = self.get_action_result('Queues', token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(501))

    def test_that_action_with_events_returns_events(self):
        result = self.action('QueueStatus')

        assert_that(result, contains(
            has_entries({
                'Response': 'Success',
                'EventList': 'start',
                'Message': 'Queue status will follow'
            }),
            has_entries({
                'Event': 'QueueParams',
                'Queue': 'my_queue',
                'Max': '0',
                'Strategy': 'ringall',
                'Calls': '0',
                'Holdtime': '0',
                'TalkTime': '0',
                'Completed': '0',
                'Abandoned': '0',
                'ServiceLevel': '0',
                'ServicelevelPerf': '0.0',
                'Weight': '0',
            }),
            has_entries({
                'Event': 'QueueStatusComplete',
                'EventList': 'Complete',
                'ListItems': '1'
            })))


class TestAuthentication(BaseIntegrationTest):

    asset = 'http_only'

    def test_that_actions_is_authenticated(self):
        result = self.get_action_result('Ping', token='invalid')

        assert_that(result.status_code, equal_to(401))
