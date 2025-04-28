# -*- coding: utf-8 -*-
"""
Rest Login module
"""
from trytond.pool import Pool

# Import the routes to register them
from . import routes

__all__ = ['register']


def register():
    # No models to register for this module
    # Routes are automatically registered through import
    Pool.register(
        module='rest_login', type_='model')
    Pool.register(
        module='rest_login', type_='wizard')
    Pool.register(
        module='rest_login', type_='report')
