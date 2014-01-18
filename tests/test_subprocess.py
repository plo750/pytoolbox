# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

import six
from nose.tools import assert_equal, assert_raises
from pytoolbox.unittest import Mock
from pytoolbox.subprocess import cmd, screen_launch, screen_list, screen_kill
from pytoolbox.validation import validate_list


class TestSubprocess(object):

    def main(self):
        self.test_screen()

    def test_cmd(self):
        log = Mock()
        cmd([u'echo', u'it seem to work'], log=log)
        assert_equal(cmd(u'cat missing_file', fail=False, log=log)[u'returncode'], 1)
        validate_list(log.call_args_list, [
            r"call\(u*'Execute echo it seem to work'\)",
            r"call\(u*'Execute cat missing_file'\)",
            r"call\(u*'Attempt 1 out of 1: Failed'\)"
        ])
        assert(cmd(u'my.funny.missing.script.sh', fail=False)[u'stderr'] != u'')
        result = cmd(u'cat {0}'.format(__file__))
        # There are at least 30 lines in this source file !
        assert(len(result[u'stdout'].splitlines()) > 30)

    def test_cmd_missing_binary(self):
        assert_equal(cmd(u'hfuejnvwqkdivengz', fail=False)[u'returncode'], 2)

    def test_retry_first_try(self):
        log = Mock()
        cmd(u'ls', log=log, tries=5, delay_min=1, delay_max=1)
        validate_list(log.call_args_list, [
            r"call\(u*'Execute ls'\)"
        ])

    def test_retry_missing_binary_no_retry(self):
        log = Mock()
        assert_raises(OSError, cmd, u'hfuejnvwqkdivengz', log=log, tries=5)
        validate_list(log.call_args_list, [
            r"call\(u*'Execute hfuejnvwqkdivengz'\)",
            r"call\(FileNotFoundError.*\)" if six.PY3 else r"call\(OSError.*\)"
        ])

    def test_retry_no_success(self):
        log = Mock()
        cmd(u'ls hfuejnvwqkdivengz', log=log, fail=False, tries=5, delay_min=0.0, delay_max=0.95)
        validate_list(log.call_args_list, [
            r"call\(u*'Execute ls hfuejnvwqkdivengz'\)",
            r"call\(u*'Attempt 1 out of 5: Will retry in 0\.[0-9]+ seconds'\)",
            r"call\(u*'Attempt 2 out of 5: Will retry in 0\.[0-9]+ seconds'\)",
            r"call\(u*'Attempt 3 out of 5: Will retry in 0\.[0-9]+ seconds'\)",
            r"call\(u*'Attempt 4 out of 5: Will retry in 0\.[0-9]+ seconds'\)",
            r"call\(u*'Attempt 5 out of 5: Failed'\)"
        ])

    def test_screen(self):
        try:
            # Launch some screens
            screen_kill(u'my_1st_screen', fail=False)
            screen_kill(u'my_2nd_screen', fail=False)
            assert_equal(len(screen_launch(u'my_1st_screen', u'top', fail=False)[u'stderr']), 0)
            assert_equal(len(screen_launch(u'my_2nd_screen', u'top', fail=False)[u'stderr']), 0)
            assert_equal(len(screen_launch(u'my_2nd_screen', u'top', fail=False)[u'stderr']), 0)
            # List the launched screen sessions
            screens = screen_list(name=u'my_1st_screen')
            assert(len(screens) >= 1 and screens[0].endswith(u'my_1st_screen'))
            screens = screen_list(name=u'my_2nd_screen')
            assert(len(screens) >= 1 and screens[0].endswith(u'my_2nd_screen'))
        finally:
            # Cleanup
            log = Mock()
            screen_kill(name=u'my_1st_screen', log=log)
            screen_kill(name=u'my_2nd_screen', log=log)
            if log.call_args_list:
                validate_list(log.call_args_list, [
                    r"call\(u*'Execute screen -ls my_1st_screen'\)",
                    r"call\(u*'Attempt 1 out of 1: Failed'\)",
                    r"call\(u*'Execute screen -S \d+\.my_1st_screen -X quit'\)",
                    r"call\(u*'Execute screen -ls my_2nd_screen'\)",
                    r"call\(u*'Attempt 1 out of 1: Failed'\)",
                    r"call\(u*'Execute screen -S \d+\.my_2nd_screen -X quit'\)",
                    r"call\(u*'Execute screen -S \d+\.my_2nd_screen -X quit'\)"
                ])
