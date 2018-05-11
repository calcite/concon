#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `concon` package."""


import unittest

from click.testing import CliRunner

from concon import cli


class TestConcon(unittest.TestCase):
    """Tests for `concon` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'Usage: ' in result.output

        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert 'Show this message and exit.' in help_result.output
