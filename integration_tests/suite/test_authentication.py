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

from hamcrest import assert_that
from hamcrest import contains_string
from hamcrest import equal_to

from .base import BaseIntegrationTest
from .base import VALID_TOKEN


class TestAuthentication(BaseIntegrationTest):

    asset = 'http_only'

    def test_no_auth_gives_401(self):
        result = self.post_action_result('ping', token=None)

        assert_that(result.status_code, equal_to(401))

    def test_valid_auth_gives_result(self):
        result = self.post_action_result('ping', token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(200))

    def test_invalid_auth_gives_401(self):
        result = self.post_action_result('ping', token='invalid-token')

        assert_that(result.status_code, equal_to(401))


class TestAuthenticationError(BaseIntegrationTest):

    asset = 'no_auth_server'

    def test_no_auth_server_gives_503(self):
        result = self.post_action_result('ping', token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(503))
        assert_that(result.json()['details']['auth_server_host'], equal_to('inexisting-auth-server'))
        assert_that(result.json()['details']['auth_server_port'], equal_to(9497))
