# -*- coding: utf-8 -*-


from atlassian_connect_django.backends.common import compiler

class SQLCompiler(compiler.SQLCompiler):
    query_param = 'cql'
